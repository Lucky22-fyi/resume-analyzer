import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3:latest"

def get_llm_suggestions(resume_text, jd_text, matched_skills, missing_skills, ats_score):
    
    prompt = f"""You are an expert HR consultant.
ATS Score: {ats_score}/100
Matched Skills: {', '.join(matched_skills) if matched_skills else 'None'}
Missing Skills: {', '.join(missing_skills) if missing_skills else 'None'}

Return in this exact format:
SUMMARY: <2 line summary>
SUGGESTIONS:
- <suggestion 1>
- <suggestion 2>
- <suggestion 3>
- <suggestion 4>"""

    try:
        print(f" Calling ollama... URL: {OLLAMA_URL}")
        
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )
        
        print(f" Ollama response status: {response.status_code}")
        print(f" Raw response: {response.text[:200]}")

        if response.status_code == 200:
            result = response.json()
            raw_text = result.get("response", "")
            return parse_llm_response(raw_text)
        else:
            print(f" Ollama error: {response.status_code}")
            return None

    except requests.exceptions.ConnectionError as e:
        print(f" Connection Error: {e}")
        return None
    except requests.exceptions.Timeout as e:
        print(f" Timeout Error: {e}")
        return None
    except Exception as e:
        print(f" Unknown Error: {e}")
        return None


def parse_llm_response(text):
    summary = ""
    suggestions = []

    lines = text.strip().split("\n")

    in_suggestions = False
    summary_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("SUMMARY:"):
            summary_lines.append(line.replace("SUMMARY:", "").strip())
            in_suggestions = False

        elif line.startswith("SUGGESTIONS:"):
            in_suggestions = True

        elif in_suggestions and (line.startswith("- ") or line.startswith("* ")):
            suggestions.append(line[2:].strip())

        elif not in_suggestions and summary_lines and not line.startswith("SUGGESTIONS"):
            summary_lines.append(line)

    summary = " ".join(summary_lines).strip()

    # Agar suggestions nahi mile toh text se extract karo
    if not suggestions:
        for line in lines:
            line = line.strip()
            if line.startswith("- ") or line.startswith("* "):
                suggestions.append(line[2:].strip())

    return {
        "summary": summary if summary else text[:200],
        "suggestions": suggestions[:4]
    }