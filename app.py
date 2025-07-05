@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "file" not in request.files:
        return "No file uploaded", 400

    file = request.files["file"]
    if file.filename == "":
        return "Empty filename", 400

    tier = request.form.get("tier", "Free").capitalize()
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(input_path)

    try:
        import requests

        with open(input_path, "rb") as f:
            response = requests.post(
                "https://whisper-api-974376892558.asia-southeast1.run.app/transcribe",
                files={"file": f},
            )

        if response.status_code != 200:
            return f"Transcription failed: {response.text}", 500

        transcript_text = response.json().get("text", "")
    except Exception as e:
        return f"Transcription failed: {str(e)}", 500

    doc_filename = f"Transcript_{os.path.splitext(file.filename)[0]}.docx"
    doc_path = os.path.join(OUTPUT_FOLDER, doc_filename)
    generate_transcript_docx(transcript_text, doc_path, file.filename, tier)

    return send_file(doc_path, as_attachment=True)
