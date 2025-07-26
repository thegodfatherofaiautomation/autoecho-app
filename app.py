import os
import stripe
import tempfile
import datetime
from flask import Flask, request, jsonify, redirect, render_template
from werkzeug.utils import secure_filename
from pydub.utils import mediainfo
from google.cloud import firestore
from google.oauth2 import service_account

# Init Flask app
app = Flask(__name__)

# Stripe keys from environment
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY")
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")

# Setup Firestore
credentials = service_account.Credentials.from_service_account_file(
    "your_google_firestore_key.json"
)
db = firestore.Client(project="modern-bond-464518-t1", credentials=credentials)

# Allowed file types
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'flac', 'ogg'}

# Duration limits per tier (in seconds)
DURATION_LIMITS = {
    "free": 30,
    "basic": 1800,      # 30 minutes
    "standard": 5400,   # 90 minutes
    "premium": 10800    # 3 hours
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET'])
def upload():
    return render_template('upload.html')

@app.route('/process', methods=['POST'])
def process_audio():
    if 'audio_file' not in request.files or 'user_email' not in request.form:
        return "Missing audio file or email", 400

    file = request.files['audio_file']
    user_email = request.form['user_email'].lower().strip()

    if not allowed_file(file.filename):
        return "Unsupported file type", 400

    # Retrieve tier from Firestore
    user_doc = db.collection('users').document(user_email).get()
    tier = user_doc.to_dict().get('tier') if user_doc.exists else 'free'
    limit = DURATION_LIMITS.get(tier, 30)

    # Save file temporarily
    filename = secure_filename(file.filename)
    with tempfile.NamedTemporaryFile(delete=False, suffix=filename) as temp:
        file.save(temp.name)
        info = mediainfo(temp.name)
        duration = float(info['duration'])

        if duration > limit:
            return f"<h2>Audio too long for your plan.</h2><p>Max allowed: {limit // 60} minutes</p>", 400

        # Placeholder transcription
        result = f"Transcribed ({duration:.1f}s): Mock transcription result."

    return f"<h2>Transcription Result</h2><pre>{result}</pre><p><a href='/'>Back to Home</a></p>"

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
        return f"<h2>Internal Server Error</h2><p>{str(e)}</p>", 500

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.data
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except Exception as e:
        return f"Webhook error: {str(e)}", 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_email = session.get('customer_email')
        subscription_id = session.get('subscription')

        if customer_email and subscription_id:
            try:
                sub = stripe.Subscription.retrieve(subscription_id)
                price_id = sub['items']['data'][0]['price']['id']
                tier_map = {
                    "price_1RepAvEILZ6IOlsNOTCb6Vvt": "basic",
                    "price_1RepIzEILZ6IOlsNYVloChoL": "standard",
                    "price_1RepJkEILZ6IOlsNKu7ThOYd": "premium"
                }
                tier = tier_map.get(price_id, "free")

                # Store in Firestore
                db.collection('users').document(customer_email.lower()).set({
                    "tier": tier,
                    "updated": datetime.datetime.utcnow()
                })
            except Exception as e:
                print(f"[ERROR] Failed to update Firestore: {str(e)}")

    return jsonify({"status": "success"})

@app.route('/success')
def success():
    return render_template("success.html")

@app.route('/cancel')
def cancel():
    return render_template("cancel.html")

@app.route('/terms')
def terms():
    return render_template("terms.html")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
