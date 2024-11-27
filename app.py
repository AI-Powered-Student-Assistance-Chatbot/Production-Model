from flask import Flask, render_template, request, session, jsonify
import os
import json
import csv
import datetime
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import nltk
import ssl

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Download and setup
ssl._create_default_https_context = ssl._create_unverified_context
nltk.data.path.append(os.path.abspath("nltk_data"))
nltk.download('punkt')

# Load intents from JSON
file_path = os.path.abspath("./intents.json")
with open(file_path, "r") as file:
    intents = json.load(file)

# Vectorizer and model setup
vectorizer = TfidfVectorizer()
clf = LogisticRegression(random_state=0, max_iter=10000)

# Preprocess data
tags = []
patterns = []
for intent in intents:
    for pattern in intent['patterns']:
        tags.append(intent['tag'])
        patterns.append(pattern)

# Train model
x = vectorizer.fit_transform(patterns)
y = tags
clf.fit(x, y)

def chatbot_response(input_text):
    """Generates a response from the chatbot based on user input."""
    input_text = vectorizer.transform([input_text])
    tag = clf.predict(input_text)[0]
    for intent in intents:
        if intent['tag'] == tag:
            response = random.choice(intent['responses'])
            return response
    return "Sorry, I didn't understand that."

# Routes
@app.route('/')
def home():
    """Renders the homepage and initializes chat history."""
    if 'chat_history' not in session:
        session['chat_history'] = []
    return render_template('index.html', chat_history=session['chat_history'])

@app.route('/get_response', methods=['POST'])
def get_response():
    """Handles user input, generates a response, and stores the conversation."""
    user_input = request.json.get('user_input', '')
    
    if not user_input.strip():
        return jsonify({'response': "Please enter a valid message."})

    response = chatbot_response(user_input)

    # Save conversation to session
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    chat_message = {'user': user_input, 'bot': response, 'timestamp': timestamp}
    session['chat_history'].append(chat_message)

    # Optionally, store conversation to a CSV log
    with open('chat_log.csv', 'a', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow([user_input, response, timestamp])

    return jsonify({'response': response})

@app.route('/get_history', methods=['GET'])
def get_history():
    """Returns chat history."""
    chat_history = session.get('chat_history', [])
    return jsonify({'history': chat_history})

@app.route('/about')
def about():
    """Renders the About page."""
    return render_template('about.html')

@app.route('/history')
def conversation_history():
    conversation = []
    try:
        # Read the chat log CSV file
        with open('chat_log.csv', 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            next(csv_reader)  # Skip the header row
            for row in csv_reader:
                conversation.append({
                    'user': row[0],
                    'bot': row[1],
                    'timestamp': row[2]
                })
    except FileNotFoundError:
        # Handle missing file gracefully
        conversation = None

    # Render the conversation history template
    return render_template('history.html', conversation=conversation)

if __name__ == "__main__":
    # Ensure chat log file exists with headers
    if not os.path.exists('chat_log.csv'):
        with open('chat_log.csv', 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(['User Input', 'Chatbot Response', 'Timestamp'])

    app.run(debug=True)
