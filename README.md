
# 🚀 Flask Application Setup Guide  

This guide outlines the steps to set up and run a Flask application, including creating a virtual environment, installing dependencies, and configuring database connectivity.  

---

## 📌 **Step 1: Create a Virtual Environment**  
1. Open your terminal.  
2. Navigate to the project directory:  
   ```bash
   cd path/to/your/project
   ```
3. Create a virtual environment:  
   ```bash
   python -m venv venv
   ```
4. Activate the virtual environment:  
   - **Windows:**  
     ```bash
     .\venv\Scripts\activate
     ```
   - **Linux/Mac:**  
     ```bash
     source venv/bin/activate
     ```

---

## 📌 **Step 2: Install Dependencies**  
1. Make sure `requirements.txt` exists in the project directory.  
2. Install the dependencies:  
   ```bash
   pip install -r requirements.txt
   ```

---

## 📌 **Step 3: Set Up Database Connectivity**  
1. Update the database URL in the configuration file (e.g., `config.py`):  
   - Example:  
     ```python
     DATABASE_URL = 'postgresql://username:password@localhost:5432/dbname'
     ```  
2. Check if the database exists:  
   - If it doesn't exist, create the database manually or through code.  
3. Check if the required tables exist:  
   - If not, create the tables using schema definitions.  

---

## 📌 **Step 4: Run the Flask Application**  
1. Run the Flask application:  
   ```bash
   python app.py
   ```

---

## 📌 **Step 5: Test the Application**  
1. Open your browser and visit:  
   ```
   http://127.0.0.1:5000
   ```
2. Check the logs to confirm the app is running without errors.  

---

## 🎯 **Done!** Your Flask application is now up and running! 😎  
