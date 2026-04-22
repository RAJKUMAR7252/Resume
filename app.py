from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__)

# --- DATABASE CONFIGURATION ---
# Common for XAMPP: user is 'root', password is '', host is 'localhost'
db_config = { 
    'host': 'localhost', 
    'user': 'root', 
    'password': 'Rajkumar@1234',  
    'database': 'resume_db'
}

def get_db_connection(): 
    return mysql.connector.connect(**db_config)

def init_db(): 
    # Step 1: Connect to MySQL server to ensure the database exists
    try:
        conn = mysql.connector.connect(
            host=db_config['host'], 
            user=db_config['user'], 
            password=db_config['password']
        )
        cursor = conn.cursor() 
        cursor.execute("CREATE DATABASE IF NOT EXISTS resume_db") 
        cursor.close() 
        conn.close() 

        # Step 2: Connect to the specific database and create tables
        conn = get_db_connection() 
        cursor = conn.cursor() 
        
        cursor.execute(""" 
            CREATE TABLE IF NOT EXISTS candidates ( 
                id INT AUTO_INCREMENT PRIMARY KEY, 
                full_name VARCHAR(100), 
                email VARCHAR(100), 
                phone VARCHAR(20), 
                linkedin VARCHAR(100), 
                summary TEXT 
            ) 
        """) 
        
        cursor.execute(""" 
            CREATE TABLE IF NOT EXISTS education ( 
                id INT AUTO_INCREMENT PRIMARY KEY, 
                candidate_id INT, 
                degree VARCHAR(100), 
                school VARCHAR(100), 
                year VARCHAR(20), 
                FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE 
            ) 
        """) 
        
        cursor.execute(""" 
            CREATE TABLE IF NOT EXISTS experience ( 
                id INT AUTO_INCREMENT PRIMARY KEY, 
                candidate_id INT, 
                job_title VARCHAR(100), 
                company VARCHAR(100), 
                duration VARCHAR(50), 
                description TEXT, 
                FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE 
            ) 
        """) 
        
        cursor.execute(""" 
            CREATE TABLE IF NOT EXISTS skills ( 
                id INT AUTO_INCREMENT PRIMARY KEY, 
                candidate_id INT, 
                skill_name VARCHAR(255), 
                FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE 
            ) 
        """) 
        
        conn.commit() 
        conn.close()
        print("Database initialized successfully.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")

# Initialize database on startup
init_db()

@app.route('/')
def index(): 
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit_resume(): 
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    linkedin = request.form.get('linkedin')
    summary = request.form.get('summary')
    
    # Process multiple inputs (split by new lines)
    degrees = request.form.get('degrees', '').split('\n')
    schools = request.form.get('schools', '').split('\n')
    years = request.form.get('years', '').split('\n')
    
    jobs = request.form.get('jobs', '').split('\n')
    companies = request.form.get('companies', '').split('\n')
    durations = request.form.get('durations', '').split('\n')
    descriptions = request.form.get('descriptions', '').split('\n')
    
    skills_raw = request.form.get('skills', '')
    skill_list = [s.strip() for s in skills_raw.split(',') if s.strip()]

    conn = get_db_connection() 
    cursor = conn.cursor() 
    
    # Insert Candidate
    cursor.execute(""" 
        INSERT INTO candidates (full_name, email, phone, linkedin, summary) 
        VALUES (%s, %s, %s, %s, %s) 
    """, (full_name, email, phone, linkedin, summary))
    
    candidate_id = cursor.lastrowid 

    # Insert Education
    for i in range(len(degrees)): 
        if degrees[i].strip(): 
            cursor.execute(""" 
                INSERT INTO education (candidate_id, degree, school, year) 
                VALUES (%s, %s, %s, %s) 
            """, (candidate_id, degrees[i].strip(), 
                  schools[i].strip() if i < len(schools) else '', 
                  years[i].strip() if i < len(years) else '')) 

    # Insert Experience
    for i in range(len(jobs)): 
        if jobs[i].strip(): 
            cursor.execute(""" 
                INSERT INTO experience (candidate_id, job_title, company, duration, description) 
                VALUES (%s, %s, %s, %s, %s) 
            """, (candidate_id, jobs[i].strip(), 
                  companies[i].strip() if i < len(companies) else '', 
                  durations[i].strip() if i < len(durations) else '', 
                  descriptions[i].strip() if i < len(descriptions) else '')) 

    # Insert Skills
    for s in skill_list: 
        cursor.execute("INSERT INTO skills (candidate_id, skill_name) VALUES (%s, %s)", (candidate_id, s)) 

    conn.commit() 
    conn.close() 
    return redirect(url_for('view_resume', candidate_id=candidate_id))

@app.route('/resume/<int:candidate_id>')
def view_resume(candidate_id): 
    conn = get_db_connection() 
    cursor = conn.cursor(dictionary=True) 
    
    cursor.execute("SELECT * FROM candidates WHERE id = %s", (candidate_id,)) 
    candidate = cursor.fetchone() 
    
    cursor.execute("SELECT * FROM education WHERE candidate_id = %s", (candidate_id,)) 
    education = cursor.fetchall() 
    
    cursor.execute("SELECT * FROM experience WHERE candidate_id = %s", (candidate_id,)) 
    experience = cursor.fetchall() 
    
    cursor.execute("SELECT * FROM skills WHERE candidate_id = %s", (candidate_id,)) 
    skills_data = cursor.fetchall() 
    
    skills = ", ".join([s['skill_name'] for s in skills_data]) 
    conn.close() 
    
    return render_template('resume.html', candidate=candidate, education=education, experience=experience, skills=skills)

if __name__ == '__main__': 
    app.run(debug=True)