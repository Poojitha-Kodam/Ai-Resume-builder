from flask import Flask, request, jsonify, send_file, render_template, url_for, send_from_directory
import pdfkit
import os
import glob
import time
from flask_cors import CORS
import spacy

app = Flask(__name__,
    static_folder='static',
    template_folder='templates'
)
CORS(app, origins=["http://localhost:5173"])

nlp = spacy.load("en_core_web_sm")

# Ensure this path is valid for your environment
config = pdfkit.configuration(wkhtmltopdf="C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe")

output_folder = os.path.join(os.getcwd(), "output")
os.makedirs(output_folder, exist_ok=True)

# Each template now includes a "template_file" key which maps to the corresponding HTML file
templates = [
    {"id": 1, "name": "Software Engineering - Entry Level", "image": "template1_se_entry.png", "domain": "Software Engineering", "experience": "Entry Level", "template_file": "template1.html"},
    {"id": 2, "name": "Software Engineering - Mid Level", "image": "template2_se_mid.png", "domain": "Software Engineering", "experience": "Mid Level", "template_file": "template2.html"},
    {"id": 3, "name": "Software Engineering - Senior Level", "image": "template3_se_senior.png", "domain": "Software Engineering", "experience": "Senior Level", "template_file": "template3.html"},
    {"id": 4, "name": "Data Science - Entry Level", "image": "template4_ds_entry.png", "domain": "Data Science", "experience": "Entry Level", "template_file": "template4.html"},
    {"id": 5, "name": "Data Science - Mid Level", "image": "template5_ds_mid.png", "domain": "Data Science", "experience": "Mid Level", "template_file": "template5.html"},
    {"id": 6, "name": "Data Science - Senior Level", "image": "template6_ds_senior.png", "domain": "Data Science", "experience": "Senior Level", "template_file": "template6.html"},
    {"id": 7, "name": "Product Management - Entry Level", "image": "template7_pm_entry.png", "domain": "Product Management", "experience": "Entry Level", "template_file": "template7.html"},
    {"id": 8, "name": "Product Management - Mid Level", "image": "template8_pm_mid.png", "domain": "Product Management", "experience": "Mid Level", "template_file": "template8.html"},
    {"id": 9, "name": "Product Management - Senior Level", "image": "template9_pm_senior.png", "domain": "Product Management", "experience": "Senior Level", "template_file": "template9.html"},
]

@app.route("/")
def home():
    return "Flask server is running!"

@app.route('/static/images/<path:filename>')
def serve_image(filename):
    try:
        return send_from_directory(os.path.join(app.static_folder, 'images'), filename)
    except FileNotFoundError:
        return send_from_directory(os.path.join(app.static_folder, 'images'), 'fallback.png')

def clean_output_folder():
    try:
        pdf_files = sorted(
            glob.glob(os.path.join(output_folder, "*.pdf")),
            key=os.path.getctime
        )
        if len(pdf_files) > 4:
            files_to_delete = pdf_files[:-4]
            for pdf in files_to_delete:
                os.remove(pdf)
                print(f"🗑️ Deleted old PDF: {os.path.basename(pdf)}")
    except Exception as e:
        print(f"⚠️ Error while cleaning output folder: {e}")

@app.route("/get-templates", methods=["POST"])
def get_templates():
    try:
        data = request.json
        domain = data.get("domain")
        experience = data.get("experience")
        print(f"Received request for domain: {domain}, experience: {experience}")
        
        matched_templates = [
            t for t in templates
            if t["domain"].lower() == domain.lower() and t["experience"].lower() == experience.lower()
        ]
        print(f"Matched templates: {matched_templates}")
        return jsonify({"templates": matched_templates})
    except Exception as e:
        print(f"❌ Error fetching templates: {e}")
        return jsonify({"message": "Failed to fetch templates", "error": str(e)}), 500

@app.route("/generate-resume", methods=["POST"])
def generate_resume():
    try:
        data = request.json
        print("Received data for resume generation:", data)

        template_id = int(data.get("template", 1))
        selected_template = next((t for t in templates if t["id"] == template_id), templates[0])
        print(f"Selected Template: {selected_template['name']}")

        # Use the "template_file" from the selected template
        template_file = selected_template.get("template_file", f"template{template_id}.html")
        template_path = os.path.join(app.template_folder, template_file)
        if not os.path.exists(template_path):
            print(f"❌ Template file not found: {template_path}")
            return jsonify({"message": "Template file not found", "error": f"File {template_file} does not exist"}), 404

        rendered_html = render_template(
            template_file,
            name=data.get("name", "John Doe"),
            title=data.get("title", "Software Engineer"),
            contactInfo=data.get("contactInfo", {}),
            summary=data.get("summary", "Highly motivated professional..."),
            workExperience=data.get("workExperience", []),
            education=data.get("education", []),
            skills=data.get("skills", ["Leadership", "Problem-Solving"]),
            certifications=data.get("certifications", ["Certified Scrum Master"]),
            projects=data.get("projects", [{"name": "Project Alpha", "description": "Led project delivery..."}]),
            languages=data.get("languages", "English (Fluent), Spanish (Intermediate)"),
            achievements=data.get("achievements", "Recognized for exceptional performance..."),
            image_url=url_for('static', filename=f'images/{selected_template["image"]}', _external=True)
        )
        print("Rendered HTML:", rendered_html)

        # Generate PDF
        timestamp = int(time.time())
        pdf_filename = f"output_resume_{timestamp}.pdf"
        pdf_path = os.path.join(output_folder, pdf_filename)
        print(f"Saving PDF to: {pdf_path}")

        options = {
            "enable-local-file-access": None,
            "page-size": "A4",
            "encoding": "UTF-8",
            "margin-top": "10mm",
            "margin-right": "10mm",
            "margin-bottom": "10mm",
            "margin-left": "10mm",
        }

        pdfkit.from_string(rendered_html, pdf_path, configuration=config, options=options)

        if os.path.exists(pdf_path):
            print(f"✅ PDF generated successfully: {pdf_path}")
            return jsonify({"message": "Resume generated successfully!", "download_link": f"/download-resume/{pdf_filename}"})
        else:
            print("❌ Error: PDF file not found after generation.")
            return jsonify({"message": "Failed to generate PDF"}), 500
    
    except Exception as e:
        print(f"❌ Error generating resume: {e}")
        return jsonify({"message": "Failed to generate resume", "error": str(e)}), 500

@app.route("/download-resume/<filename>", methods=["GET"])
def download_resume(filename):
    pdf_path = os.path.join(output_folder, filename)
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True, mimetype="application/pdf")
    else:
        return jsonify({"message": "Resume not found"}), 404

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == "__main__":
    app.run(debug=True)
