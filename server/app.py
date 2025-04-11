from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_mail import Mail, Message
import fitz  # PyMuPDF
import os
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
CORS(app)

# ---------------- Mail Config ----------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'dangerdeva992005@gmail.com'
app.config['MAIL_PASSWORD'] = 'sorx redd ovti hmhy'  # For production, use environment variables!

mail = Mail(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- Utility Functions ----------------

def extract_text_from_pdf(filepath):
    """Extract all text from a PDF file."""
    text = ""
    with fitz.open(filepath) as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_skills(text):
    """Extract relevant skills from resume text."""
    keywords = ["Python", "JavaScript", "React", "HTML", "CSS", "SQL", "Machine Learning", "TensorFlow", "Figma", "Kotlin"]
    return [kw for kw in keywords if kw.lower() in text.lower()]

def check_ats_friendly(filepath, extracted_text):
    """Check resume for ATS-friendliness based on images and keywords."""
    with fitz.open(filepath) as doc:
        images = sum(len(page.get_images(full=True)) for page in doc)

    keywords = extract_skills(extracted_text)
    ats_score = 100
    suggestions = []

    if images > 0:
        ats_score -= 20
        suggestions.append("Avoid using images in resume.")

    if len(keywords) < 3:
        ats_score -= 30
        suggestions.append("Add more job-relevant keywords like Python, HTML, etc.")

    return {
        "score": ats_score,
        "suggestions": suggestions,
        "keywords_found": keywords
    }

def match_career_twins(user_skills):
    """Find top 3 career twin matches based on skill overlap."""
    with open("career_twins.json") as f:
        twin_data = json.load(f)

    matches = []
    for twin in twin_data:
        score = len(set(user_skills).intersection(set(twin["skills"])))
        if score >= 2:
            twin["match_score"] = score
            matches.append(twin)

    matches.sort(key=lambda x: x["match_score"], reverse=True)
    return matches[:3]

# ---------------- Routes ----------------

@app.route('/upload', methods=['POST'])
def upload_resume():
    """Handles resume upload and returns parsed data."""
    if 'resume' not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files['resume']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    extracted_text = extract_text_from_pdf(filepath)
    ats_result = check_ats_friendly(filepath, extracted_text)
    user_skills = ats_result["keywords_found"]
    career_twins = match_career_twins(user_skills)

    return jsonify({
        "message": "Resume uploaded and parsed!",
        "resume_text": extracted_text[:1000],  # Truncated preview
        "ats_result": ats_result,
        "career_twins": career_twins
    }), 200

@app.route('/download-report', methods=['POST'])
def download_report():
    """Generates and returns ATS report PDF."""
    data = request.json
    filename = os.path.join(UPLOAD_FOLDER, "ats_report.pdf")

    c = canvas.Canvas(filename, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "ATS Resume Report")

    c.setFont("Helvetica", 12)
    c.drawString(50, 720, f"ATS Score: {data['score']} / 100")
    c.drawString(50, 700, f"Matched Keywords: {', '.join(data['keywords'])}")

    y = 680
    if data["suggestions"]:
        c.drawString(50, y, "Suggestions:")
        y -= 20
        for suggestion in data["suggestions"]:
            c.drawString(60, y, f"- {suggestion}")
            y -= 20

    c.save()
    return send_file(filename, as_attachment=True)

@app.route('/send-email', methods=['POST'])
def send_email():
    """Sends ATS report via email."""
    data = request.json
    email = data['email']
    pdf_path = os.path.join(UPLOAD_FOLDER, "ats_report.pdf")

    if not os.path.exists(pdf_path):
        return jsonify({"message": "PDF not found"}), 404

    msg = Message("Your ATS Resume Report",
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[email])
    msg.body = "Attached is your ATS resume report. Thank you for using ResumeTwin!"

    with app.open_resource(pdf_path) as pdf:
        msg.attach("ATS_Report.pdf", "application/pdf", pdf.read())

    try:
        mail.send(msg)
        return jsonify({"message": "Email sent successfully!"}), 200
    except Exception as e:
        return jsonify({"message": f"Failed to send email: {str(e)}"}), 500

@app.route('/suggest-skills', methods=['POST'])
def suggest_skills():
    """Suggest missing skills for a given job role."""
    data = request.json
    resume_text = data.get('resume_text', '')
    job_role = data.get('job_role', '')

    resume_skills = extract_skills(resume_text)

    try:
        with open('skills_db.json') as f:
            db = json.load(f)
    except Exception as e:
        return jsonify({"error": f"Failed to load skills DB: {str(e)}"}), 500

    expected_skills = db.get(job_role, [])
    matched_skills = [skill for skill in expected_skills if skill in resume_skills]
    suggested_skills = [skill for skill in expected_skills if skill not in resume_skills]

    return jsonify({
        "matched_skills": matched_skills,
        "suggested_skills": suggested_skills
    }), 200

@app.route('/growth-path', methods=['POST'])
def growth_path():
    data = request.json
    text = data.get("resume_text", "").lower()

    try:
        with open('growth_roadmap.json') as file:
            roadmap_data = json.load(file)
    except Exception as e:
        return jsonify({"error": f"Failed to load roadmap: {str(e)}"}), 500

    matched_path = None
    matched_skills = []
    missing_skills = []

    for path, details in roadmap_data.items():
        path_skills = []

        # Safely extract and normalize skills
        resources = details.get("resources", [])
        for item in resources:
            if isinstance(item, dict):
                title = item.get("title")
                if title:
                    path_skills.append(title.strip())
            elif isinstance(item, str):
                path_skills.append(item.strip())

        path_skills += [tool.strip() for tool in details.get("tools", []) if isinstance(tool, str)]
        path_skills += [proj.strip() for proj in details.get("projects", []) if isinstance(proj, str)]

        # Remove duplicates and None values
        path_skills = list(set(filter(None, path_skills)))

        # Match logic
        found = [skill for skill in path_skills if skill.lower() in text]
        if len(found) >= 2:
            matched_path = path
            matched_skills = found
            missing_skills = list(set(path_skills) - set(found))
            break

    if not matched_path:
        return jsonify({"message": "Couldn't identify a clear career path from the resume."}), 404

    return jsonify({
        "career_path": matched_path,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills
    }), 200
import json

def clean_growth_roadmap(file_path):
    with open(file_path, 'r') as file:
        roadmap = json.load(file)

    cleaned_roadmap = {}

    for path, details in roadmap.items():
        cleaned_details = {
            "resources": [],
            "projects": [],
            "tools": []
        }

        # Clean resources
        resources = details.get("resources", [])
        for res in resources:
            if isinstance(res, dict):
                title = res.get("title")
                if title and isinstance(title, str):
                    cleaned_details["resources"].append({"title": title.strip()})
            elif isinstance(res, str) and res.strip():
                cleaned_details["resources"].append(res.strip())

        # Clean projects
        projects = details.get("projects", [])
        cleaned_details["projects"] = [p.strip() for p in projects if isinstance(p, str) and p.strip()]

        # Clean tools
        tools = details.get("tools", [])
        cleaned_details["tools"] = [t.strip() for t in tools if isinstance(t, str) and t.strip()]

        cleaned_roadmap[path] = cleaned_details

    with open("cleaned_growth_roadmap.json", "w") as outfile:
        json.dump(cleaned_roadmap, outfile, indent=4)

    print("✅ Cleaned roadmap saved as 'cleaned_growth_roadmap.json'.")

# Run it
clean_growth_roadmap("growth_roadmap.json")


# ---------------- Start Server ----------------

if __name__ == '__main__':
    app.run(debug=True)
