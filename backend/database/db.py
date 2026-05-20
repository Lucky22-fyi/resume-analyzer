import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "resume_analyzer.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Candidate table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidate_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            job_description TEXT,
            ats_score REAL,
            selection_probability REAL,
            skills_match TEXT,
            missing_skills TEXT,
            summary TEXT,
            suggestions TEXT,
            llm_used INTEGER DEFAULT 0,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Recruiter table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recruiter_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_description TEXT,
            total_resumes INTEGER,
            top_candidate TEXT,
            top_score REAL,
            all_results TEXT,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()