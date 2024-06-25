from flask import Flask, request, jsonify
from transformers import pipeline
import re
from datetime import datetime, timedelta

app = Flask(__name__)

# Load the NLP model
chatbot = pipeline('conversational', model='facebook/blenderbot-400M-distill')

# In-memory storage for reminders
reminders = []

def add_reminder(text):
    """Extract reminder details from text and add to the reminders list."""
    match = re.search(r'remind me to (.+?) in (\d+) (second|minute|hour|day|week)s?', text, re.IGNORECASE)
    if match:
        task = match.group(1)
        amount = int(match.group(2))
        unit = match.group(3)
        
        if unit == 'second':
            reminder_time = datetime.now() + timedelta(seconds=amount)
        elif unit == 'minute':
            reminder_time = datetime.now() + timedelta(minutes=amount)
        elif unit == 'hour':
            reminder_time = datetime.now() + timedelta(hours=amount)
        elif unit == 'day':
            reminder_time = datetime.now() + timedelta(days=amount)
        elif unit == 'week':
            reminder_time = datetime.now() + timedelta(weeks=amount)
        
        reminders.append({'task': task, 'time': reminder_time})
        return f"Reminder set for {task} in {amount} {unit}(s)."
    else:
        return "Sorry, I couldn't understand the reminder."

@app.route('/')
def home():
    return '''
        <h1>Home Assistant Chatbot</h1>
        <form action="/chat" method="post" id="chat-form">
            <input type="text" name="message" placeholder="Enter your message" id="message-input">
            <input type="submit" value="Send">
        </form>
        <button onclick="startRecognition()">Speak</button>
        <p id="response"></p>
        <script>
            function startRecognition() {
                var recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                recognition.lang = 'en-US';
                recognition.onresult = function(event) {
                    document.getElementById('message-input').value = event.results[0][0].transcript;
                    document.getElementById('chat-form').submit();
                };
                recognition.start();
            }

            document.getElementById('chat-form').onsubmit = function(event) {
                event.preventDefault();
                var message = document.getElementById('message-input').value;
                fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: 'message=' + encodeURIComponent(message),
                })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('response').innerText = data.response;
                });
            };
        </script>
    '''

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.form['message'].lower()
    
    if 'remind me to' in user_message:
        bot_message = add_reminder(user_message)
    else:
        response = chatbot(user_message)
        bot_message = response[0]['generated_text']
    
    return jsonify({'response': bot_message})

@app.route('/reminders', methods=['GET'])
def get_reminders():
    """Endpoint to list all reminders (for debugging purposes)."""
    now = datetime.now()
    due_reminders = [reminder for reminder in reminders if reminder['time'] <= now]
    for reminder in due_reminders:
        reminders.remove(reminder)
    return jsonify(due_reminders)

if __name__ == '__main__':
    app.run(debug=True)
