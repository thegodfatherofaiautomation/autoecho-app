from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("landing.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/upload")
def upload():
    return render_template("upload.html")

@app.route("/transcript")
def transcript():
    # placeholder values
    return render_template("transcript.html", filename="example.mp3", tier="Free", transcript_file="output/example.txt")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
