import os
import pandas as pd
import google.generativeai as genai
import sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from rapidfuzz import process
import json
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from flask import Flask, request, jsonify, render_template, session
import datetime
import csv
# Add to imports
from werkzeug.utils import secure_filename
import tempfile

import speech_recognition as sr


app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with your actual secret key

# Load Gemini API Key securely
os.environ["GEMINI_API_KEY"] = "AIzaSyAy0IUrqWfBs6ITZvjU3F8Hq31l-EPqD6o"  # Replace with your actual API key

def configure_gemini_api():
    try:
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        return genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 1000,
                "response_mime_type": "text/plain",
            },
        )
    except Exception as e:
        return None

chat_model = configure_gemini_api()

# Database configuration
DATABASE_URL = "mysql+pymysql://root@localhost:3306/collegedata"  # Replace with your actual details

def fetch_data_from_db(query, params=None):
    """Fetch data from the database."""
    try:
        engine = sqlalchemy.create_engine(DATABASE_URL)
        with engine.connect() as connection:
            if params:
                return pd.read_sql(query, connection, params=params)
            return pd.read_sql(query, connection)
    except Exception as e:
        return f"Error fetching data from database: {str(e)}"

# Define a mapping of keywords to tables
table_mapping = {
    "placement": "sanjivaniplacementinfo",
    "admission": "admission_requirements",
    "department": "department_details",
    "cutoff": "admission_requirements",
    "score":"admission_requirements",
    "faculty": "department_details",
    "professor": "department_details",
    "fees": "admission_requirements",
    "intake":"admission_requirements",
}

# Function to interact with Gemini API
def ask_gemini(prompt):
    try:
        chat_session = chat_model.start_chat(history=[])
        response = chat_session.send_message(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error with Gemini API: {str(e)}"



# Function to find the closest match for keywords
def find_closest_match(query, options, threshold=50):
    if not query or not options:
        return None

    closest_match = process.extractOne(query, options)
    if closest_match:
        match, score = closest_match[:2]
        return match if score >= threshold else None
    return None

# Load intents and preprocess for fallback
file_path = os.path.abspath("./intents.json")
with open(file_path, "r") as file:
    intents = json.load(file)

vectorizer = TfidfVectorizer()
clf = LogisticRegression(random_state=0, max_iter=10000)

patterns, tags = [], []
for intent in intents:
    for pattern in intent['patterns']:
        patterns.append(pattern)
        tags.append(intent['tag'])

x = vectorizer.fit_transform(patterns)
y = tags
clf.fit(x, y)

# Generate fallback response
def check_intents_for_fallback(user_query, threshold=85):
    best_score, best_response = 0, None
    user_query_lower = user_query.lower()  # Convert user query to lowercase
    
    for intent in intents:
        # Normalize intent patterns to lowercase for matching
        patterns_lower = [pattern.lower() for pattern in intent.get("patterns", [])]
        match = process.extractOne(user_query_lower, patterns_lower)
        
        if match:
            matched_pattern, score = match[:2]
            if score > best_score:
                best_score = score
                best_response = random.choice(intent.get("responses", []))

    if best_score >= threshold:
        return best_response
    return "Sorry, I couldn't understand that. Could you rephrase?"

# Process user query
def process_query(user_query):
    keywords = list(table_mapping.keys())
    matched_keyword = find_closest_match(user_query.lower(), keywords)  # Convert query to lowercase

    if matched_keyword:
        table_name = table_mapping[matched_keyword]
        query = f"SELECT * FROM {table_name}"
        db_data = fetch_data_from_db(query)

        if isinstance(db_data, str) and "Error" in db_data:
            return db_data
        elif db_data.empty:
            return check_intents_for_fallback(user_query)

        #Summarize and use Gemini to generate a response
        data_summary = db_data.to_string(index=False)
        prompt = f"Here is the data from the table {table_name}: {data_summary}. Answer the query: {user_query}"
        return ask_gemini(prompt)

        

    return check_intents_for_fallback(user_query)

# Flask Routes
@app.route("/")
def home():
    if "chat_history" not in session:
        session["chat_history"] = []
    return render_template("bot_entry.html", chat_history=session["chat_history"])

@app.route("/index")
def index_page():
    if "chat_history" not in session:
        session["chat_history"] = []
    return render_template("index.html", chat_history=session["chat_history"])

@app.route("/get_response", methods=["POST"])
def get_response():
    user_input = request.json.get("user_input", "").strip()

    if not user_input:
        return jsonify({"response": "Please enter a valid message."})

    user_input = user_input.lower()  # Normalize the user input to lowercase
    response = process_query(user_input)

    #admin

    # Save conversation to session
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    chat_message = {"user": user_input, "bot": response, "timestamp": timestamp}
    session["chat_history"].append(chat_message)

    # Optionally, store conversation to a CSV log
    with open("chat_log.csv", "a", newline="", encoding="utf-8") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow([user_input, response, timestamp])

    return jsonify({"response": response})

@app.route('/admin', methods=['GET'])
def show_placements():
    page = request.args.get('page', 1, type=int)  # Get the page number from the URL
    per_page = 10  # Number of records per page
    placements = SanjivaniPlacementInfo.query.paginate(page=page, per_page=per_page, error_out=False)
    print(placements)
    return render_template('admin_panel.html', placements=placements)


@app.route('/admin', methods=['POST'])
def admin_panel_post():
    """Handles POST requests for the Admin Panel"""
    form_type = request.form.get('form_type')
    if form_type == 'placement':
        try:
            query = """
                INSERT INTO sanjivaniplacementinfo
                (Student_Name, Batch, Placement_Type, Name_Of_Company, department)
                VALUES (:Student_Name, :Batch, :Placement_Type, :Name_Of_Company, :department)
            """
            values = {
                'Student_Name': request.form['name_of_student'],
                'Batch': request.form['batch'],
                'Placement_Type': request.form['placementtype'],
                'Name_Of_Company': request.form['company'],
                'department': request.form['department']
            }

            engine = sqlalchemy.create_engine(DATABASE_URL)
            with engine.begin() as conn:
                conn.execute(sqlalchemy.text(query), values)

            # ✅ Query placement data correctly
            page = request.args.get('page', 1, type=int)
            per_page = 10
            placements = SanjivaniPlacementInfo.query.paginate(page=page, per_page=per_page, error_out=False)
    
            return render_template('admin_panel.html', placements=placements, message="Placement added successfully!")

        except Exception as e:
            page = request.args.get('page', 1, type=int)
            per_page = 10
            placements = SanjivaniPlacementInfo.query.paginate(page=page, per_page=per_page, error_out=False)
    
            return render_template('admin_panel.html', placements=placements, error=f"Error inserting placement data: {str(e)}")
    return render_template('admin_panel.html')

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)


class SanjivaniPlacementInfo(db.Model):
    __tablename__ = 'sanjivaniplacementinfo'
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    batch = db.Column(db.String(20), nullable=False)
    placement_type = db.Column(db.String(50), nullable=False)
    name_of_company = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)



@app.route("/get_history", methods=["GET"])
def get_history():
    chat_history = session.get("chat_history", [])
    return jsonify({"history": chat_history})

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/history")
def conversation_history():
    conversation = []
    try:
        with open("chat_log.csv", "r", encoding="utf-8") as csvfile:
            csv_reader = csv.reader(csvfile)
            next(csv_reader)  # Skip the header row
            for row in csv_reader:
                conversation.append({"user": row[0], "bot": row[1], "timestamp": row[2]})
    except FileNotFoundError:
        conversation = None

    return render_template("history.html", conversation=conversation)

# Main entry point
if __name__ == "__main__":
    if not os.path.exists("chat_log.csv"):
        with open("chat_log.csv", "w", newline="", encoding="utf-8") as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["User Input", "Chatbot Response", "Timestamp"])

    app.run(debug=True)