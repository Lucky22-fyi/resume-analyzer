import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import requests
import json

from services.parser import extract_text
from services.analyzer import analyze_resume
from database.db import init_db
from database.models import (
    save_candidate_result,
    save_recruiter_result,
    get_candidate_history,
    get_recruiter_history,
    delete_candidate_record,
    delete_recruiter_record
)

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

init_db()

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3:latest"

# ─── CANDIDATE: Analyze ───────────────────────────────────────────
@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        file = request.files.get("resume")
        jd = request.form.get("job_description", "")

        if not file:
            return jsonify({"error": "Resume required"}), 400
        if not jd.strip():
            return jsonify({"error": "Job Description required"}), 400
        if not file.filename.endswith(".pdf"):
            return jsonify({"error": "Only PDF allowed"}), 400

        filename = secure_filename(file.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)

        resume_text = extract_text(path)
        if not resume_text.strip():
            return jsonify({"error": "Could not extract text from PDF"}), 400

        result = analyze_resume(resume_text, jd)
        save_candidate_result(filename, jd, result)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── RECRUITER: Analyze Multiple ─────────────────────────────────
@app.route("/analyze-multiple", methods=["POST"])
def analyze_multiple():
    try:
        files = request.files.getlist("resumes")
        jd = request.form.get("job_description", "")

        if not files:
            return jsonify({"error": "Resumes required"}), 400
        if not jd.strip():
            return jsonify({"error": "Job Description required"}), 400

        results = []
        for file in files:
            filename = secure_filename(file.filename)
            path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(path)
            resume_text = extract_text(path)
            result = analyze_resume(resume_text, jd)
            result["name"] = filename.replace(".pdf", "").replace("_", " ")
            results.append(result)

        results.sort(key=lambda x: x["ats_score"], reverse=True)
        save_recruiter_result(jd, results)
        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── CANDIDATE: History ───────────────────────────────────────────
@app.route("/candidate/history", methods=["GET"])
def candidate_history():
    try:
        data = get_candidate_history()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── RECRUITER: History ───────────────────────────────────────────
@app.route("/recruiter/history", methods=["GET"])
def recruiter_history():
    try:
        data = get_recruiter_history()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── DELETE: Candidate Record ────────────────────────────────────
@app.route("/candidate/history/<int:record_id>", methods=["DELETE"])
def delete_candidate(record_id):
    try:
        delete_candidate_record(record_id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── DELETE: Recruiter Record ────────────────────────────────────
@app.route("/recruiter/history/<int:record_id>", methods=["DELETE"])
def delete_recruiter(record_id):
    try:
        delete_recruiter_record(record_id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── AI PROGRESS ANALYSIS ────────────────────────────────────────
@app.route("/candidate/ai-progress", methods=["POST"])
def ai_progress():
    try:
        body = request.get_json()
        history = body.get("history", [])

        if len(history) < 2:
            return jsonify({
                "analysis": "Kam se kam 2 analyses honi chahiye progress dekhne ke liye. Pehle apna resume analyze karein!"
            })

        # History summary banao Ollama ke liye
        history_summary = ""
        for i, item in enumerate(reversed(history)):
            history_summary += f"""
Analysis #{i+1} (Date: {item['analyzed_at']}):
- ATS Score: {item['ats_score']}/100
- Selection Probability: {item['selection_probability']}%
- Matched Skills: {', '.join(item['skills_match']) if item['skills_match'] else 'None'}
- Missing Skills: {', '.join(item['missing_skills']) if item['missing_skills'] else 'None'}
- Summary: {item['summary']}
"""

        prompt = f"""You are an expert career coach and resume consultant.

A candidate has submitted their resume multiple times for analysis. Here is their complete history from oldest to newest:

{history_summary}

Based on this progression, provide a detailed progress report covering:

1. IMPROVEMENTS: What has genuinely improved between analyses?
2. DECLINED: What got worse or what new problems appeared?
3. CONSISTENT WEAKNESSES: What skills or areas have remained weak throughout?
4. BEST PERFORMANCE: Which analysis was their strongest and why?
5. ACTION PLAN: Top 4 specific things they must do next to improve their resume score significantly.

Return EXACTLY in this format:
IMPROVEMENTS:
- <point>
- <point>

DECLINED:
- <point>
- <point>

CONSISTENT WEAKNESSES:
- <point>
- <point>

BEST PERFORMANCE:
<one line about best analysis>

ACTION PLAN:
- <specific action 1>
- <specific action 2>
- <specific action 3>
- <specific action 4>

Be specific, honest, and practical. No extra text."""

        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL_NAME,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120
            )

            if response.status_code == 200:
                raw = response.json().get("response", "")
                return jsonify({"analysis": raw, "llm_used": True})
            else:
                return jsonify({
                    "analysis": generate_basic_progress(history),
                    "llm_used": False
                })

        except Exception:
            return jsonify({
                "analysis": generate_basic_progress(history),
                "llm_used": False
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def generate_basic_progress(history):
    """Ollama na ho to basic NLP progress report"""
    oldest = history[-1]
    newest = history[0]
    diff = newest['ats_score'] - oldest['ats_score']

    lines = []
    lines.append(f"IMPROVEMENTS:")
    if diff > 0:
        lines.append(f"- ATS Score {diff:.1f} points badha hai ({oldest['ats_score']} → {newest['ats_score']})")
    else:
        lines.append("- Abhi tak koi significant improvement nahi dikh rahi")

    new_skills = set(newest['skills_match']) - set(oldest['skills_match'])
    if new_skills:
        lines.append(f"- Naye matched skills: {', '.join(new_skills)}")

    lines.append(f"\nDECLINED:")
    if diff < 0:
        lines.append(f"- ATS Score {abs(diff):.1f} points gira hai")
    lost_skills = set(oldest['skills_match']) - set(newest['skills_match'])
    if lost_skills:
        lines.append(f"- Yeh skills ab match nahi ho rahe: {', '.join(lost_skills)}")
    if not lost_skills and diff >= 0:
        lines.append("- Koi major decline nahi")

    lines.append(f"\nCONSISTENT WEAKNESSES:")
    common_missing = set(oldest['missing_skills']) & set(newest['missing_skills'])
    if common_missing:
        for s in list(common_missing)[:3]:
            lines.append(f"- '{s}' skill consistently missing hai")
    else:
        lines.append("- Missing skills mein improvement ho rahi hai")

    best = max(history, key=lambda x: x['ats_score'])
    lines.append(f"\nBEST PERFORMANCE:")
    lines.append(f"Best ATS Score {best['ats_score']}/100 tha — {best['analyzed_at']} ko")

    lines.append(f"\nACTION PLAN:")
    if newest['missing_skills']:
        lines.append(f"- In skills ko resume mein add karo: {', '.join(newest['missing_skills'][:3])}")
    lines.append("- Resume mein strong action verbs use karo (Developed, Built, Implemented)")
    lines.append("- Projects section mein technologies clearly mention karo")
    lines.append("- JD ke keywords ko resume mein naturally include karo")

    return "\n".join(lines)


if __name__ == "__main__":
    app.run(debug=True)