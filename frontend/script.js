document.getElementById("analyzeBtn").onclick = async function () {
    const file = document.getElementById("resumeInput").files[0];
    const jd = document.getElementById("jd_input").value.trim();
    const resultBox = document.getElementById("result");

    if (!jd) { alert("Job Description daalo!"); return; }
    if (!file) { alert("Resume upload karo!"); return; }

    const formData = new FormData();
    formData.append("resume", file);
    formData.append("job_description", jd);

    resultBox.style.display = "block";
    resultBox.innerHTML = "<p>Analyzing...  Please wait (AI processing ho raha hai)</p>";

    try {
        const res = await fetch("http://127.0.0.1:5000/analyze", {
            method: "POST",
            body: formData
        });

        const data = await res.json();

        if (data.error) {
            resultBox.innerHTML = `<p> ${data.error}</p>`;
            return;
        }

        const scoreClass = data.ats_score > 70 ? "good" : data.ats_score > 40 ? "mid" : "bad";

        resultBox.innerHTML = `
            <div class="${data.llm_used ? 'llm-badge' : 'llm-badge nlp-only'}">
                ${data.llm_used ? ' AI Enhanced (Llama3 + NLP)' : '📊 NLP Analysis Only'}
            </div>

            <h3> Analysis Result</h3>

            <div class="score-box">
                <div class="score-item">
                    <span class="score-label">ATS Score</span>
                    <span class="score-value ${scoreClass}">${data.ats_score}/100</span>
                </div>
                <div class="score-item">
                    <span class="score-label">Selection Probability</span>
                    <span class="score-value ${scoreClass}">${data.selection_probability}%</span>
                </div>
            </div>

            <div class="section">
                <h4> Summary</h4>
                <p>${data.summary}</p>
            </div>

            <div class="section">
                <h4> Matched Skills (${data.skills_match.length})</h4>
                <div class="skills-container">
                    ${data.skills_match.length > 0
                        ? data.skills_match.map(s => `<span class="skill-tag match">${s}</span>`).join("")
                        : "<span class='none-text'>No skills matched</span>"}
                </div>
            </div>

            <div class="section">
                <h4> Missing Skills (${data.missing_skills.length})</h4>
                <div class="skills-container">
                    ${data.missing_skills.length > 0
                        ? data.missing_skills.map(s => `<span class="skill-tag missing">${s}</span>`).join("")
                        : "<span class='none-text'>None! Great job </span>"}
                </div>
            </div>

            <div class="section">
                <h4> Suggestions</h4>
                <ul>
                    ${data.suggestions.map(s => `<li>${s}</li>`).join("")}
                </ul>
            </div>
        `;

    } catch (err) {
        resultBox.innerHTML = `<p> Server connect nahi ho raha. <br>Run karo: <code>python app.py</code></p>`;
    }
};