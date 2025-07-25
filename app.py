import os
import stripe
import tempfile
import wave
import contextlib
from flask import Flask, request, jsonify, redirect, render_template
from werkzeug.utils import secure_filename
from pydub import AudioSegment

app = Flask(__name__)

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY")
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")

ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'flac', 'ogg'}
PLAN_LIMITS = {
    "free": 90,
    "basic": 300,
    "standard": 900,
    "premium": 1800
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_audio_duration(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext in ['.mp3', '.m4a', '.flac', '.ogg']:
            audio = AudioSegment.from_file(filepath)
            return len(audio) / 1000  # ms to seconds
        elif ext == '.wav':
            with contextlib.closing(wave.open(filepath, 'r')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                return frames / float(rate)
    except Exception:
        return None
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET'])
def upload():
    return render_template('upload.html')

@app.route('/process', methods=['POST'])
def process_audio():
    if 'audio_file' not in request.files:
        return "No file part", 400

    file = request.files['audio_file']
    plan = request.form.get('plan', 'free')

    if file.filename == '':
        return "No selected file", 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        with tempfile.NamedTemporaryFile(delete=False, suffix=filename) as temp:
            file.save(temp.name)

            duration = get_audio_duration(temp.name)
            if duration is None:
                return "<h2>Error processing audio file duration</h2>", 400

            limit = PLAN_LIMITS.get(plan, 90)
            if duration > limit:
                return f"""
                    <h2>Audio Too Long</h2>
                    <p>Your current plan <strong>({plan.title()})</strong> allows up to {limit} seconds.</p>
                    <p>This file is {int(duration)} seconds long.</p>
                    <a href='/upload'>Try a shorter file</a>
                """

            result = f"✅ Mock transcription for file: {filename} (duration: {int(duration)}s)"
            return f"<h2>Transcription Result</h2><pre>{result}</pre><p><a href='/'>Back to Home</a></p>"

    return "Unsupported file type", 400

@app.route('/buy/<tier>')
def buy(tier):
    prices = {
        "basic": "price_1RepAvEILZ6IOlsNOTCb6Vvt",
        "standard": "price_1RepIzEILZ6IOlsNYVloChoL",
        "premium": "price_1RepJkEILZ6IOlsNKu7ThOYd"
    }

    if tier not in prices:
        return "Invalid plan", 400

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{
                "price": prices[tier],
                "quantity": 1,
            }],
            customer_creation='always',
            success_url="https://autoecho.xyz/success",
            cancel_url="https://autoecho.xyz/cancel",
        )
        return redirect(session.url, code=303)
    except Exception as e:
        print(f"[ERROR] Stripe session creation failed: {str(e)}")
        return f"<h2>Internal Server Error</h2><p>{str(e)}</p>", 500

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.data
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        return "Invalid signature", 400
    except Exception as e:
        return f"Webhook error: {str(e)}", 400

    event_type = event['type']
    print(f"[DEBUG] Stripe event received: {event_type}")
    return jsonify({"status": "success"})

@app.route('/success')
def success():
    return "<h1>✅ Payment successful!</h1><p>You can now upload longer audio files.</p><a href='/'>Back to Home</a>"

@app.route('/cancel')
def cancel():
    return "<h1>❌ Payment canceled.</h1><p>No worries! You can still try our Free Mode below.</p><a href='/'>Back to Home</a>"

@app.route('/terms')
def terms():
    return render_template('terms.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
