from services.nlp_engine import calculate_similarity
from utils.text_cleaner import clean_text
from services.llm_engine import get_llm_suggestions

SKILLS = {
    "python": ["python"],
    "java": ["java"],
    "c++": ["c++"],
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning"],
    "artificial intelligence": ["artificial intelligence", "ai"],
    "data science": ["data science"],
    "data analysis": ["data analysis"],
    "sql": ["sql"],
    "html": ["html"],
    "css": ["css"],
    "javascript": ["javascript", "js"],
    "react": ["react"],
    "node": ["node", "nodejs"],
    "flask": ["flask"],
    "django": ["django"],
    "api": ["api", "rest api"],
    "backend": ["backend", "server"],
    "frontend": ["frontend", "ui"],
    "git": ["git"],
    "docker": ["docker"],
    "ios": ["ios"],
    "swift": ["swift"],
    "objective c": ["objective c"],
    "xcode": ["xcode"],
    "mobile development": ["mobile", "mobile development"]
}


def extract_skills(text):
    found = set()
    for skill, variants in SKILLS.items():
        for v in variants:
            if v in text:
                found.add(skill)
    return list(found)


def analyze_resume(resume_text, jd_text):

    if not resume_text or resume_text.strip() == "":
        return {
            "ats_score": 0,
            "selection_probability": 0,
            "skills_match": [],
            "missing_skills": [],
            "summary": "Resume text could not be extracted properly.",
            "suggestions": ["Use a proper text-based PDF resume"],
            "llm_used": False
        }

    clean_resume = clean_text(resume_text)
    clean_jd = clean_text(jd_text)

    # NLP scoring
    similarity_score = calculate_similarity(clean_resume, clean_jd)
    resume_skills = extract_skills(clean_resume)
    jd_skills = extract_skills(clean_jd)
    jd_skills = jd_skills[:6]

    matching_skills = list(set(resume_skills) & set(jd_skills))
    missing_skills = list(set(jd_skills) - set(resume_skills))

    if len(jd_skills) > 0:
        skill_score = (len(matching_skills) / len(jd_skills)) * 100
    else:
        skill_score = 0

    ats_score = (0.7 * skill_score) + (0.3 * similarity_score)

    if len(matching_skills) >= 3:
        ats_score += 15
    if len(matching_skills) <= 1:
        ats_score *= 0.6

    ats_score = max(0, min(100, round(ats_score, 2)))
    selection_probability = round(ats_score * 0.9, 2)

    # Default NLP summary & suggestions
    summary = f"Resume matches approximately {ats_score}% of job requirements."
    suggestions = []
    if missing_skills:
        suggestions.append("Add missing skills: " + ", ".join(missing_skills))
    if ats_score < 40:
        suggestions.append("Low match. Improve skills alignment.")
    elif ats_score < 70:
        suggestions.append("Moderate match. Improve keyword targeting.")
    else:
        suggestions.append("Strong profile! Keep it up.")

    llm_used = False

    # LLM suggestions try
    llm_result = get_llm_suggestions(
        resume_text, jd_text,
        matching_skills, missing_skills,
        ats_score
    )

    if llm_result:
        if llm_result.get("summary"):
            summary = llm_result["summary"]
        if llm_result.get("suggestions"):
            suggestions = llm_result["suggestions"]
        llm_used = True

    return {
        "ats_score": ats_score,
        "selection_probability": selection_probability,
        "skills_match": matching_skills,
        "missing_skills": missing_skills,
        "summary": summary,
        "suggestions": suggestions,
        "llm_used": llm_used
    }