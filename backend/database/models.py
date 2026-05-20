import json
from database.db import get_connection

def save_candidate_result(filename, jd, result):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO candidate_history 
        (filename, job_description, ats_score, selection_probability, 
         skills_match, missing_skills, summary, suggestions, llm_used)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        filename,
        jd,
        result.get("ats_score", 0),
        result.get("selection_probability", 0),
        json.dumps(result.get("skills_match", [])),
        json.dumps(result.get("missing_skills", [])),
        result.get("summary", ""),
        json.dumps(result.get("suggestions", [])),
        1 if result.get("llm_used") else 0
    ))
    conn.commit()
    conn.close()

def save_recruiter_result(jd, results):
    conn = get_connection()
    cursor = conn.cursor()
    top = results[0] if results else {}
    cursor.execute('''
        INSERT INTO recruiter_history 
        (job_description, total_resumes, top_candidate, top_score, all_results)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        jd,
        len(results),
        top.get("name", "N/A"),
        top.get("ats_score", 0),
        json.dumps(results)
    ))
    conn.commit()
    conn.close()

def get_candidate_history():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM candidate_history ORDER BY analyzed_at DESC')
    rows = cursor.fetchall()
    conn.close()
    result = []
    for row in rows:
        result.append({
            "id": row["id"],
            "filename": row["filename"],
            "job_description": row["job_description"],
            "ats_score": row["ats_score"],
            "selection_probability": row["selection_probability"],
            "skills_match": json.loads(row["skills_match"]),
            "missing_skills": json.loads(row["missing_skills"]),
            "summary": row["summary"],
            "suggestions": json.loads(row["suggestions"]),
            "llm_used": bool(row["llm_used"]),
            "analyzed_at": row["analyzed_at"]
        })
    return result

def get_recruiter_history():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM recruiter_history ORDER BY analyzed_at DESC')
    rows = cursor.fetchall()
    conn.close()
    result = []
    for row in rows:
        result.append({
            "id": row["id"],
            "job_description": row["job_description"],
            "total_resumes": row["total_resumes"],
            "top_candidate": row["top_candidate"],
            "top_score": row["top_score"],
            "all_results": json.loads(row["all_results"]),
            "analyzed_at": row["analyzed_at"]
        })
    return result

def delete_candidate_record(record_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM candidate_history WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()

def delete_recruiter_record(record_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM recruiter_history WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()