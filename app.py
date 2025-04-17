# import os
# import pandas as pd
# import google.generativeai as genai
# import sqlalchemy
# from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy import text
# from rapidfuzz import process
# import json
# import random
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.linear_model import LogisticRegression
# from flask import Flask, flash, request, jsonify, render_template, session
# import datetime
# import csv
# # Add to imports
# from werkzeug.utils import secure_filename
# import tempfile

# import speech_recognition as sr


# app = Flask(__name__)
# app.secret_key = "your_secret_key"  # Replace with your actual secret key
# DATABASE_URL = "mysql+pymysql://root@localhost:3306/collegedata"  # Replace with your actual details

# # Load Gemini API Key securely
# os.environ["GEMINI_API_KEY"] = "AIzaSyAy0IUrqWfBs6ITZvjU3F8Hq31l-EPqD6o"  # Replace with your actual API key
# app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# db = SQLAlchemy(app)


# def configure_gemini_api():
#     try:
#         genai.configure(api_key=os.environ["GEMINI_API_KEY"])
#         return genai.GenerativeModel(
#             model_name="gemini-1.5-flash",
#             generation_config={
#                 "temperature": 0.7,
#                 "top_p": 0.95,
#                 "top_k": 40,
#                 "max_output_tokens": 1000,
#                 "response_mime_type": "text/plain",
#             },
#         )
#     except Exception as e:
#         return None

# chat_model = configure_gemini_api()

# # Database configuration

# def fetch_data_from_db(query, params=None):
#     """Fetch data from the database."""
#     try:
#         engine = sqlalchemy.create_engine(DATABASE_URL)
#         with engine.connect() as connection:
#             if params:
#                 return pd.read_sql(query, connection, params=params)
#             return pd.read_sql(query, connection)
#     except Exception as e:
#         return f"Error fetching data from database: {str(e)}"

# # Define a mapping of keywords to tables
# table_mapping = {
#     "placement": "sanjivaniplacementinfo",
#     "admission": "admission_requirements",
#     "department": "department_details",
#     "cutoff": "admission_requirements",
#     "score":"admission_requirements",
#     "faculty": "department_details",
#     "professor": "department_details",
#     "fees": "admission_requirements",
#     "intake":"admission_requirements",
# }

# # Function to interact with Gemini API
# def ask_gemini(prompt):
#     try:
#         chat_session = chat_model.start_chat(history=[])
#         response = chat_session.send_message(prompt)
#         return response.text.strip()
#     except Exception as e:
#         return f"Error with Gemini API: {str(e)}"



# # Function to find the closest match for keywords
# def find_closest_match(query, options, threshold=50):
#     if not query or not options:
#         return None

#     closest_match = process.extractOne(query, options)
#     if closest_match:
#         match, score = closest_match[:2]
#         return match if score >= threshold else None
#     return None

# # Load intents and preprocess for fallback
# file_path = os.path.abspath("./intents.json")
# with open(file_path, "r") as file:
#     intents = json.load(file)

# vectorizer = TfidfVectorizer()
# clf = LogisticRegression(random_state=0, max_iter=10000)

# patterns, tags = [], []
# for intent in intents:
#     for pattern in intent['patterns']:
#         patterns.append(pattern)
#         tags.append(intent['tag'])

# x = vectorizer.fit_transform(patterns)
# y = tags
# clf.fit(x, y)

# # Generate fallback response
# def check_intents_for_fallback(user_query, threshold=85):
#     best_score, best_response = 0, None
#     user_query_lower = user_query.lower()  # Convert user query to lowercase
    
#     for intent in intents:
#         # Normalize intent patterns to lowercase for matching
#         patterns_lower = [pattern.lower() for pattern in intent.get("patterns", [])]
#         match = process.extractOne(user_query_lower, patterns_lower)
        
#         if match:
#             matched_pattern, score = match[:2]
#             if score > best_score:
#                 best_score = score
#                 best_response = random.choice(intent.get("responses", []))

#     if best_score >= threshold:
#         return best_response
#     return "Sorry, I couldn't understand that. Could you rephrase?"

# def fetch_data_from_db(query, params=None):
#     """Fetch data from the database with improved error handling."""
#     try:
#         engine = sqlalchemy.create_engine(DATABASE_URL)
#         with engine.connect() as connection:
#             if params:
#                 result = pd.read_sql(query, connection, params=params)
#             else:
#                 result = pd.read_sql(query, connection)
#             return result
#     except Exception as e:
#         print(f"Database error: {str(e)}")  # Log the error for debugging
#         return f"Error fetching data from database: {str(e)}"

# def process_query(user_query):
#     """Process user query with improved error handling and SQL injection prevention."""
#     keywords = list(table_mapping.keys())
#     matched_keyword = find_closest_match(user_query.lower(), keywords)

#     if matched_keyword:
#         table_name = table_mapping[matched_keyword]
        
#         try:
#             # Use parametrized queries to prevent SQL injection
#             if "cutoff" in user_query.lower() and "department" in user_query.lower():
#                 # Extract department from user query
#                 dept_terms = ["it", "computer", "information", "mechanical", "civil", "electrical"]
#                 dept_query = None
                
#                 for term in dept_terms:
#                     if term in user_query.lower():
#                         dept_query = term
#                         break
                
#                 if dept_query:
#                     # Safer query using sqlalchemy text
#                     query = text(f"SELECT * FROM {table_name} WHERE LOWER(department_name) LIKE :dept")
#                     db_data = fetch_data_from_db(query, params={"dept": f"%{dept_query}%"})
#                 else:
#                     # Get all cutoff data
#                     query = text(f"SELECT * FROM {table_name}")
#                     db_data = fetch_data_from_db(query)
            
#             elif "hod" in user_query.lower() or "head" in user_query.lower():
#                 # For HOD queries, use the department_details table
#                 dept_terms = ["it", "computer", "information", "mechanical", "civil", "electrical"]
#                 dept_query = None
                
#                 for term in dept_terms:
#                     if term in user_query.lower():
#                         dept_query = term
#                         break
                
#                 table_name = "department_details"  # Force using the correct table
                
#                 if dept_query:
#                     query = text(f"SELECT * FROM {table_name} WHERE LOWER(department_name) LIKE :dept AND LOWER(position) LIKE '%hod%'")
#                     db_data = fetch_data_from_db(query, params={"dept": f"%{dept_query}%"})
#                 else:
#                     query = text(f"SELECT * FROM {table_name} WHERE LOWER(position) LIKE '%hod%'")
#                     db_data = fetch_data_from_db(query)
            
#             else:
#                 # Default query
#                 query = text(f"SELECT * FROM {table_name}")
#                 db_data = fetch_data_from_db(query)
            
#             if isinstance(db_data, str) and "Error" in db_data:
#                 return db_data
#             elif isinstance(db_data, pd.DataFrame) and db_data.empty:
#                 return check_intents_for_fallback(user_query)
            
#             # Generate an explanation using Gemini
#             data_summary = db_data.to_string(index=False)
#             prompt = f"""
#             Here is the data from the table {table_name}: {data_summary}. 
#             Answer the query: {user_query} in a little explantion manner depend upon the query otherwise not (dont mention table names, it will threat to database).
#             Here are some rules you should follow:
#             1. Do not mention the table name in the response.
#             2. Dont tell them you are using a database.
#             3. Dont tell you are Large langauge model tell them you are Sanjivani Chatbot.( if they asked )"""
#             explanation = ask_gemini(prompt)
            
#             #Provide ONLY the direct answer without describing the data structure or mentioning tables.
#             # Format the data as an HTML table with styling
#             styled_table = db_data.to_html(classes="data-table", index=False)
            
#             # Add CSS styling for the table directly in the response
#             styled_response = f"""
#             <div class="bot-response">
#                 <div class="explanation">{explanation}</div>
#                 <style>
#                     .data-table {{
#                         width: 100%;
#                         margin-top: 15px;
#                         border-collapse: collapse;
#                         font-size: 14px;
#                         background-color: white;
#                         border-radius: 8px;
#                         overflow: hidden;
#                         box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
#                     }}

#                     .data-table th {{
#                         background-color: #007bff;
#                         color: white;
#                         padding: 10px;
#                         text-align: left;
#                         border: 1px solid #ddd;
#                         font-weight: bold;
#                     }}

#                     .data-table td {{
#                         padding: 10px;
#                         border: 1px solid #ddd;
#                         color: #333;
#                     }}

#                     .data-table tr:nth-child(even) {{
#                         background-color: #f1f1f1;
#                     }}

#                     .data-table tr:nth-child(odd) {{
#                         background-color: #ffffff;
#                     }}

#                     .data-table tr:hover {{
#                         background-color: #d0eaff;
#                     }}

#                     .explanation {{
#                         margin-bottom: 10px;
#                         color: #ffffff;
#                     }}

#                     /* Sky Blue Background Below the Table */
#                     .table-container {{
#                         padding: 20px;
#                         background: linear-gradient(to bottom, #ffffff, #87CEEB);
#                         border-radius: 10px;
#                         margin-top: 20px;
#                     }}
#                 </style>
#                 {styled_table}
#             </div>
#             """

#             return styled_response
#         except Exception as e:
#             print(f"Error in process_query: {str(e)}")  # Log the error
#             return f"I apologize, but I encountered an error processing your request: {str(e)}"

#     return check_intents_for_fallback(user_query)

# # Flask Routes
# @app.route("/")
# def home():
#     if "chat_history" not in session:
#         session["chat_history"] = []
#     return render_template("bot_entry.html", chat_history=session["chat_history"])

# @app.route("/index")
# def index_page():
#     if "chat_history" not in session:
#         session["chat_history"] = []
#     return render_template("index.html", chat_history=session["chat_history"])
# @app.route('/login')
# def login():
#     return render_template('login.html')  # Show login page
# @app.route("/get_response", methods=["POST"])
# def get_response():
#     user_input = request.json.get("user_input", "").strip()

#     if not user_input:
#         return jsonify({"response": "Please enter a valid message."})

#     user_input = user_input.lower()
#     response = process_query(user_input)

#     # Save conversation to session - store HTML content as is
#     timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     chat_message = {"user": user_input, "bot": response, "timestamp": timestamp}
#     session["chat_history"].append(chat_message)

#     # For the CSV log, we should strip HTML tags for cleaner storage
#     plain_response = response
#     if "<table" in response:
#         # This is a simple way to indicate a table was included without storing the whole HTML
#         plain_response = response.split("<br><br>")[0] + " [Table data included]"
    
#     with open("chat_log.csv", "a", newline="", encoding="utf-8") as csvfile:
#         csv_writer = csv.writer(csvfile)
#         csv_writer.writerow([user_input, plain_response, timestamp])

#     return jsonify({"response": response, "has_table": "<table" in response})

# @app.route('/admin', methods=['GET'])
# def show_placements():
#     page = request.args.get('page', 1, type=int)  # Get the page number from the URL
#     per_page = 10  # Number of records per page
#     placements = SanjivaniPlacementInfo.query.paginate(page=page, per_page=per_page, error_out=False)
#     print(placements)
#     return render_template('admin_panel.html', placements=placements)


# @app.route('/admin', methods=['POST'])
# def admin_panel_post():
#     """Handles POST requests for the Admin Panel"""
#     form_type = request.form.get('form_type')
#     if form_type == 'placement':
#         try:
#             # Create new placement record
#             new_placement = SanjivaniPlacementInfo(
#                 student_name=request.form['name_of_student'],
#                 batch=request.form['batch'],
#                 placement_type=request.form['placementtype'],
#                 name_of_company=request.form['company'],
#                 department=request.form['department']
#             )

#             # Add to session and commit
#             db.session.add(new_placement)
#             db.session.commit()

#             flash("Placement added successfully!", "success") 

#             # ✅ Query placement data correctly
#             page = request.args.get('page', 1, type=int)
#             per_page = 10
#             placements = SanjivaniPlacementInfo.query.paginate(page=page, per_page=per_page, error_out=False)
    
#             return jsonify({"success": True, "message": "Placement added successfully!"})

#         except Exception as e:
#             page = request.args.get('page', 1, type=int)
#             per_page = 10
#             placements = SanjivaniPlacementInfo.query.paginate(page=page, per_page=per_page, error_out=False)
#             return jsonify({"success": False, "error": "Invalid form submission"})
#     return render_template('admin_panel.html')


# @app.route('/admin/delete/<int:id>', methods=['DELETE'])
# def delete_placement(id):
#     try:
#         placement = SanjivaniPlacementInfo.query.get_or_404(id)
#         db.session.delete(placement)
#         db.session.commit()
#         return jsonify({"success": True, "message": "Record deleted successfully"})
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({"success": False, "error": str(e)}), 500

# # New UPDATE endpoint
# @app.route('/admin/update/<int:id>', methods=['POST'])
# def update_placement(id):
#     try:
#         placement = SanjivaniPlacementInfo.query.get_or_404(id)
#         placement.student_name = request.json['name_of_student']
#         placement.batch = request.json['batch']
#         placement.placement_type = request.json['placementtype']
#         placement.name_of_company = request.json['company']
#         placement.department = request.json['department']

#         db.session.commit()

#         page = request.args.get('page', 1, type=int)
#         per_page = 10
#         placements = SanjivaniPlacementInfo.query.paginate(page=page, per_page=per_page, error_out=False)
#         return jsonify({"success": True, "message": "Placement updated successfully!"}), 200
#     except Exception as e:
#         db.session.rollback()
#         page = request.args.get('page', 1, type=int)
#         per_page = 10
#         placements = SanjivaniPlacementInfo.query.paginate(page=page, per_page=per_page, error_out=False)
#         return jsonify({"success": False, "error": str(e)}), 500  # Return JSON error response

# class SanjivaniPlacementInfo(db.Model):
#     __tablename__ = 'sanjivaniplacementinfo'
#     id = db.Column(db.Integer, primary_key=True)
#     student_name = db.Column(db.String(100), nullable=False)
#     batch = db.Column(db.String(20), nullable=False)
#     placement_type = db.Column(db.String(50), nullable=False)
#     name_of_company = db.Column(db.String(100), nullable=False)
#     department = db.Column(db.String(100), nullable=False)



# @app.route("/get_history", methods=["GET"])
# def get_history():
#     chat_history = session.get("chat_history", [])
#     return jsonify({"history": chat_history})

# @app.route("/about")
# def about():
#     return render_template("about.html")

# @app.route("/history")
# def conversation_history():
#     conversation = []
#     try:
#         with open("chat_log.csv", "r", encoding="utf-8") as csvfile:
#             csv_reader = csv.reader(csvfile)
#             next(csv_reader)  # Skip the header row
#             for row in csv_reader:
#                 conversation.append({"user": row[0], "bot": row[1], "timestamp": row[2]})
#     except FileNotFoundError:
#         conversation = None

#     return render_template("history.html", conversation=conversation)

# # Main entry point
# if __name__ == "__main__":
#     if not os.path.exists("chat_log.csv"):
#         with open("chat_log.csv", "w", newline="", encoding="utf-8") as csvfile:
#             csv_writer = csv.writer(csvfile)
#             csv_writer.writerow(["User Input", "Chatbot Response", "Timestamp"])

#     app.run(debug=True)










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
@app.route('/login')
def login():
    return render_template('login.html')  # Show login page


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