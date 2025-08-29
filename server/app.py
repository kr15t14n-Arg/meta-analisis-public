from flask import Flask, request, jsonify, send_file
import os
from werkzeug.utils import secure_filename
from tools.metadata_analyzer import analyze_common_metadata
from tools.file_analyzer import analyze_multiple_files
from tools.report_generator import generate_forensic_report

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/")
def index():
    return "Meta-Analisis Server 🕵️‍♀️ - Subí archivos vía /analyze/images o /analyze/docs"

@app.route("/analyze/images", methods=["POST"])
def analyze_images_api():
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No se enviaron archivos"}), 400

    saved_files = []
    for f in files:
        filename = secure_filename(f.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        f.save(path)
        saved_files.append(path)

    common, csv_path, rows = analyze_common_metadata(saved_files)
    report_path = generate_forensic_report(common, rows, "images_report.docx")

    return send_file(report_path, as_attachment=True)

@app.route("/analyze/docs", methods=["POST"])
def analyze_docs_api():
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No se enviaron archivos"}), 400

    saved_files = []
    for f in files:
        filename = secure_filename(f.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        f.save(path)
        saved_files.append(path)

    common, csv_path, rows = analyze_multiple_files(saved_files)
    report_path = generate_forensic_report(common, rows, "docs_report.docx")

    return send_file(report_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, port=5001)

