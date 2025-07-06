from flask import Flask, request, send_file, jsonify
import os
import uuid
import whisper
from docx import Document
from datetime import datetime
import stripe

app = Flask(__name__)

UPLOAD_FOLDER = "/tmp/uploads"
OUTPUT_FOLDER = "/tmp/outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

model = whisper.load_model("base")

# Stripe keys from environment (Google Secret Manager injects them)
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")

@app.route("/")
def index():
    return f"AutoEcho is live. Stripe Key Loaded: {'Yes' if stripe.api_key else 'No'}"

@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "file" not in request.files:
        return "No file uploaded", 400

    file = request.files["file"]
    if file.filename == "":
        return "Empty filename", 400

    if file.content_length and file.content_length > 25 * 1024 * 1024:
        return "File too large. Max size is 25MB.", 413

    tier = request.form.get("tier", "Free").capitalize()
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(input_path)

    try:
        result = model.transcribe(input_path)
        transcript_text = result["text"]
    except Exception as e:
        return f"Transcription failed: {str(e)}", 500

    doc_filename = f"Transcript_{os.path.splitext(file.filename)[0]}.docx"
    doc_path = os.path.join(OUTPUT_FOLDER, doc_filename)
    generate_transcript_docx(transcript_text, doc_path, file.filename, tier)

    return send_file(doc_path, as_attachment=True)

@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        return "Signature verification failed", 400
    except Exception as e:
        return f"Webhook error: {str(e)}", 400

    # Example webhook handling
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        print("✅ Payment completed:", session["id"])

    elif event["type"] == "invoice.payment_failed":
        print("❌ Payment failed for:", event["data"]["object"]["customer"])

    elif event["type"] == "customer.subscription.deleted":
        print("🔻 Subscription cancelled.")

    return jsonify(success=True)

def generate_transcript_docx(text, output_path, original_filename, tier):
    doc = Document()
    doc.add_heading("AutoEcho Transcription", level=1)
    doc.add_paragraph(f"File: {original_filename}")
    doc.add_paragraph(f"Tier: {tier}")
    doc.add_paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    doc.add_paragraph("")
    doc.add_paragraph(text)
    doc.save(output_path)

if __name__ == "__main__":
    app.run(debug=True)
