from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def calculate_similarity(resume_text, jd_text):
    vectorizer = TfidfVectorizer(ngram_range=(1,2))

    vectors = vectorizer.fit_transform([resume_text, jd_text])

    similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]

    return round(similarity * 100, 2)


def extract_skills(text, skill_list):
    found = []

    for skill in skill_list:
        if skill.lower() in text:
            found.append(skill)

    return list(set(found))