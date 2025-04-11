import React, { useState } from 'react';

function ResumeUpload() {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState('');
  const [resumeText, setResumeText] = useState('');
  const [atsResult, setAtsResult] = useState(null);
  const [email, setEmail] = useState('');
  const [skillSuggestions, setSkillSuggestions] = useState(null);
  const [careerTwins, setCareerTwins] = useState([]);
  const [careerPath, setCareerPath] = useState('');

  const handleFileChange = (e) => setFile(e.target.files[0]);

  const handleUpload = async () => {
    if (!file) return setMessage("Please select a file.");

    const formData = new FormData();
    formData.append("resume", file);

    try {
      const response = await fetch("http://localhost:5000/upload", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();
      setMessage(result.message);
      setResumeText(result.resume_text || '');
      setAtsResult(result.ats_result || {});
      setCareerTwins(result.career_twins || []);
    } catch (error) {
      console.error("Upload error:", error);
      setMessage("Something went wrong!");
    }
  };

  const handleSkillSuggestions = async () => {
    if (!careerPath || !resumeText) {
      alert("Please upload your resume and select a career path.");
      return;
    }

    try {
      const response = await fetch("http://localhost:5000/suggest-skills", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resume_text: resumeText,
          job_role: careerPath
        }),
      });

      const result = await response.json();
      setSkillSuggestions(result);
    } catch (error) {
      console.error("Skill suggestion error:", error);
    }
  };

  const handleDownload = async () => {
    if (!atsResult) return;

    try {
      const response = await fetch("http://localhost:5000/download-report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          score: atsResult.score,
          suggestions: atsResult.suggestions,
          keywords: atsResult.keywords_found,
        }),
      });

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "ATS_Report.pdf");
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error("Download failed", err);
    }
  };

  const handleSendEmail = async () => {
    if (!email) return alert("Enter your email address.");

    try {
      const response = await fetch("http://localhost:5000/send-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      const result = await response.json();
      alert(result.message);
    } catch (error) {
      console.error("Email send failed:", error);
    }
  };

  return (
    <div style={styles.container}>
      <h2 style={styles.heading}>📄 Upload Your Resume</h2>

      <input type="file" accept=".pdf" onChange={handleFileChange} />
      <br />
      <button style={styles.button} onClick={handleUpload}>⬆️ Upload</button>
      <p>{message}</p>
      

      {atsResult && (
        <div style={styles.resultBox}>
          <h3>📊 ATS Result</h3>
          <p><strong>Score:</strong> {atsResult.score || 0} / 100</p>
          <p><strong>Matched Keywords:</strong> {(atsResult.keywords_found || []).join(', ') || "None"}</p>
          <p><strong>Suggestions:</strong></p>
          <ul>
            {(atsResult.suggestions || []).map((s, i) => <li key={i}>{s}</li>)}
          </ul>

          <button style={styles.button} onClick={handleDownload}>📥 Download Report</button>
          <div style={{ marginTop: '15px' }}>
            <input
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={styles.input}
            />
            <button style={styles.button} onClick={handleSendEmail}>✉️ Send to Email</button>
          </div>
        </div>
      )}
      <div className="card">
  <h3>✨ ATS Score</h3>
  <p></p>
</div>


      <div style={{ marginTop: '30px' }}>
        <label><strong>🎯 Select Career Role:</strong></label>
        <select
          value={careerPath}
          onChange={(e) => setCareerPath(e.target.value)}
          style={styles.input}
        >
          <option value="">-- Choose --</option>
          <option value="Web Developer">Web Developer</option>
          <option value="Data Scientist">Data Scientist</option>
          <option value="Android Developer">Android Developer</option>
          <option value="DevOps Engineer">DevOps Engineer</option>
          <option value="UI/UX Designer">UI/UX Designer</option>
        </select>
        <button style={styles.button} onClick={handleSkillSuggestions}>💡 Get Skill Suggestions</button>
      </div>

      {skillSuggestions && (
        <div style={styles.resultBox}>
          <h3>💡 Skill Suggestions for {skillSuggestions.career_path}</h3>
          <p><strong>Matched Skills:</strong> {(skillSuggestions.matched_skills || []).join(', ') || "None"}</p>
          <p><strong>Missing/Recommended Skills:</strong> {(skillSuggestions.missing_skills || []).join(', ') || "None"}</p>
        </div>
      )}

      {resumeText && (
        <div style={styles.textBox}>
          <h3>📝 Extracted Resume Text:</h3>
          <p style={{ whiteSpace: 'pre-wrap' }}>{resumeText}</p>
        </div>
      )}

      {careerTwins.length > 0 && (
        <div style={styles.resultBox}>
          <h3>👥 Career Twin Matches</h3>
          {careerTwins.map((twin, i) => (
            <div key={i}>
              <p><strong>{twin.role}</strong> at {twin.company}</p>
              <p>Matched Skills: {(twin.skills || []).join(', ')}</p>
              <hr />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    maxWidth: "800px",
    margin: "0 auto",
    padding: "20px",
    textAlign: "center",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
  },
  
  heading: {
    fontSize: "26px",
    marginBottom: "20px",
  },
  button: {
    padding: "10px 18px",
    marginTop: "10px",
    backgroundColor: "#f7f9f9",
    color: "green",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
    marginRight: "10px",
  },
  resultBox: {
    backgroundColor: "#f9f9f9",
    borderRadius: "10px",
    padding: "20px",
    marginTop: "30px",
    boxShadow: "0 2px 8px rgba(90, 218, 103, 0.49)",
    textAlign: "left",
    width: "100%",
  },
  textBox: {
    backgroundColor: "#f9f9f9",
    borderRadius: "10px",
    padding: "20px",
    marginTop: "30px",
    boxShadow: "0 2px 8px rgba(245, 11, 202, 0.93)",
    textAlign: "left",
    width: "100%",
  },
  input: {
    padding: "8px",
    marginRight: "10px",
    border: "1px solid #ccc",
    borderRadius: "5px",
  },
  
};

export default ResumeUpload;
