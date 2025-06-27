from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)

# Landing page with login options
@app.route("/")
def home():
    return render_template("index.html")  # no redirect loop

# Stripe login route placeholder
@app.route("/login/stripe")
def login_stripe():
    return "Stripe login integration coming soon."

# PayPal login route placeholder
@app.route("/login/paypal")
def login_paypal():
    return "PayPal login integration coming soon."

# Traditional login route (if needed)
@app.route("/login")
def login():
    return render_template("login.html")

# Upload form
@app.route("/upload")
def upload():
    return render_template("upload.html")

# Transcript preview placeholder
@app.route("/transcript")
def transcript():
    # Sample placeholder values
    return render_template("transcript.html", filename="example.mp3", tier="Free", transcript_file="output/example.txt")

# Run app using Render's assigned port
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render provides this
    app.run(host="0.0.0.0", port=port, debug=False)
