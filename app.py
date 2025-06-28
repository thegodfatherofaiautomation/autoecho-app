import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
import stripe

app = Flask(__name__)

# Load environment variables
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
DOMAIN = os.getenv("DOMAIN", "http://localhost:5000")
PRICE_IDS = {
    "basic": os.getenv("STRIPE_PRICE_BASIC"),
    "standard": os.getenv("STRIPE_PRICE_STANDARD"),
    "premium": os.getenv("STRIPE_PRICE_PREMIUM")
}

stripe.api_key = STRIPE_SECRET_KEY

@app.route("/")
def index():
    return render_template("landing.html")

@app.route("/create-checkout-session/<tier>", methods=["POST"])
def create_checkout_session(tier):
    price_id = PRICE_IDS.get(tier.lower())
    if not price_id:
        return jsonify({"error": "Invalid or missing price ID"}), 400

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            success_url=f"{DOMAIN}/upload?session_id={{CHECKOUT_SESSION_ID}}&tier={tier}",
            cancel_url=f"{DOMAIN}/",
        )
        return redirect(session.url, code=303)

    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/upload")
def upload():
    return render_template("upload.html")

@app.route("/transcript")
def transcript():
    return render_template(
        "transcript.html",
        filename="example.mp3",
        tier=request.args.get("tier", "Free"),
        transcript_file="output/example.txt"
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
