from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("landing.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/login/stripe")
def login_stripe():
    # You can later integrate Stripe OAuth or redirect here
    return redirect(url_for("upload"))  # placeholder

@app.route("/login/paypal")
def login_paypal():
    # Same with PayPal OAuth redirect
    return redirect(url_for("upload"))  # placeholder

@app.route("/upload")
def upload():
    return render_template("upload.html")

@app.route("/transcript")
def transcript():
    return render_template("transcript.html", filename="example.mp3", tier="Free", transcript_file="output/example.txt")

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

