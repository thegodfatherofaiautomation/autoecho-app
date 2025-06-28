from flask import Flask, render_template, request, redirect, url_for
import os
import stripe

app = Flask(__name__)

# Stripe environment variables
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")
DOMAIN = os.getenv("DOMAIN", "https://autoecho.xyz")  # fallback

@app.route("/")
def index():
    return render_template("landing.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/login/stripe")
def login_stripe():
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[{
                'price': STRIPE_PRICE_ID,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f"{DOMAIN}/upload",
            cancel_url=f"{DOMAIN}/",
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return f"Error creating Stripe checkout session: {e}", 500

@app.route("/upload")
def upload():
    return render_template("upload.html")

@app.route("/transcript")
def transcript():
    return render_template("transcript.html", filename="example.mp3", tier="Free", transcript_file="output/example.txt")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
