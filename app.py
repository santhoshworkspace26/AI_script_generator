from flask import Flask, render_template, request, send_file
import google.generativeai as genai
from dotenv import load_dotenv
from reportlab.pdfgen import canvas
import os

load_dotenv()

app = Flask(__name__)

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")

# Store latest generated script
latest_script = ""


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():

    global latest_script

    topic = request.form["topic"]
    video_type = request.form["video_type"]
    tone = request.form["tone"]
    requirements = request.form["requirements"]
    prompt = f"""
    Create a professional video content package.

    Topic: {topic}
    Video Type: {video_type}
    Tone: {tone}

    Additional Requirements:
    {requirements}

    Return the response EXACTLY in this format:

    # Video Title

    [title]

    # Thumbnail Text

    [text]

    # AI Thumbnail Prompt

    [prompt]

    # Hook

    [hook]

    # Full Script

    [script]

    # Storyboard

    [storyboard]

    # Camera Angles

    [camera angles]

    # B-Roll Suggestions

    [b-roll ideas]

    # Hashtags

    [hashtags]

    Do not skip any section.
    Use markdown headings exactly as shown.
    """
    try:
        response = model.generate_content(prompt)

        latest_script = response.text

        return render_template(
            "result.html",
            result=response.text
        )

    except Exception:
        return render_template(
            "result.html",
            result="Gemini rate limit reached. Please wait a minute and try again."
        )


@app.route("/download")
def download():

    global latest_script

    pdf_file = "script.pdf"

    c = canvas.Canvas(pdf_file)

    text = c.beginText(40, 800)

    for line in latest_script.split("\n"):
        text.textLine(line)

    c.drawText(text)

    c.save()

    return send_file(
        pdf_file,
        as_attachment=True
    )
@app.route("/refine", methods=["POST"])
def refine():

    global latest_script

    changes = request.form["changes"]

    prompt = f"""
    Original Script:

    {latest_script}

    User Changes:

    {changes}

    Modify the existing script accordingly.
    Keep the same structured format.
    """

    response = model.generate_content(prompt)

    latest_script = response.text

    sections = parse_sections(response.text)

    return render_template(
        "result.html",
        sections=sections
    )


if __name__ == "__main__":
    app.run(debug=True)