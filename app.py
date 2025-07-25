from flask import Flask, request, render_template, redirect, url_for, session
from pydub.utils import mediainfo
from pydub import AudioSegment
import os
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Duration thresholds in seconds
TIER_LIMITS = {
    "free": 30,
    "basic": 1800,
    "standard": 5400,
    "premium": 10800
}

# Email to tier mapping (temporary until billing API integration)
USER_TIERS = {
    "free@example.com": "free",
    "basic@example.com": "basic",
    "standard@example.com": "standard",
    "premium@example.com": "premium"
}

def get_user_tier():
    email = session.get("user_email", "free@example.com")
    return USER_TIERS.get(email, "free")

def check_audio_duration(file_path, tier):
    try:
        audio = AudioSegment.from_file(file_path)
        duration_sec = len(audio) / 1000
        return duration_sec <= TIER_LIMITS.get(tier, 30)
    except Exception as e:
        print(f"Error checking duration: {e}")
        return False

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        email = request.form.get("email")
        if email:
            session["user_email"] = email
        return redirect(url_for("upload"))
    return render_template("index.html")

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file part"
        file = request.files["file"]
        if file.filename == "":
            return "No selected file"

        tier = get_user_tier()
        filepath = os.path.join("uploads", file.filename)
        file.save(filepath)

        if not check_audio_duration(filepath, tier):
            os.remove(filepath)
            return f"Upload rejected: File exceeds your tier’s max duration ({TIER_LIMITS[tier]} sec)"

        # Placeholder for transcription
        os.remove(filepath)
        return f"Transcription successful for tier: {tier}"

    return render_template("upload.html", tier=get_user_tier())

@app.route("/cancel")
def cancel():
    return render_template("cancel.html")

@app.route("/success")
def success():
    return render_template("success.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")
