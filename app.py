from flask import Flask, render_template, request, make_response
from openai import OpenAI
import json
import os

app = Flask(__name__)

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

EMERGENCY_KEYWORDS = [
    "chest pain",
    "difficulty breathing",
    "shortness of breath",
    "unconscious",
    "severe bleeding",
    "blood vomiting",
    "seizure",
    "fainting"
]

# Simple history storage
history_list = []

def check_emergency(symptoms):
    text = symptoms.lower()
    for word in EMERGENCY_KEYWORDS:
        if word in text:
            return True
    return False

def get_ai_health_response(symptoms):
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a healthcare assistant for educational purposes only. "
                        "Do not give a final diagnosis. "
                        "Return only valid JSON with these keys exactly: "
                        "possible_condition, reason, severity, basic_care, see_doctor_when, disclaimer. "
                        "Severity must be one of: Low, Medium, High. "
                        "Keep every field short, simple, and clear."
                    )
                },
                {
                    "role": "user",
                    "content": f"My symptoms are: {symptoms}"
                }
            ]
        )

        content = response.choices[0].message.content
        return json.loads(content)

    except Exception as e:
        return {
            "possible_condition": "Unable to analyze right now",
            "reason": f"Error: {str(e)}",
            "severity": "Medium",
            "basic_care": "Rest, stay hydrated, and monitor symptoms.",
            "see_doctor_when": "See a doctor if symptoms worsen or continue.",
            "disclaimer": "This is not a final medical diagnosis."
        }
@app.route('/')
def home():
    return render_template('index.html', history=history_list)

@app.route('/predict', methods=['POST'])
def predict():
    symptoms = request.form['symptoms']
    emergency = check_emergency(symptoms)
    result = get_ai_health_response(symptoms)

    # Add to history
    history_item = {
        "symptoms": symptoms,
        "condition": result["possible_condition"],
        "severity": result["severity"]
    }

    history_list.insert(0, history_item)

    # Keep only last 5 entries
    if len(history_list) > 5:
        history_list.pop()

    return render_template(
        'index.html',
        user_input=symptoms,
        result=result,
        emergency=emergency,
        history=history_list
    )

@app.route('/download-report', methods=['POST'])
def download_report():
    symptoms = request.form['symptoms']
    possible_condition = request.form['possible_condition']
    reason = request.form['reason']
    severity = request.form['severity']
    basic_care = request.form['basic_care']
    see_doctor_when = request.form['see_doctor_when']
    disclaimer = request.form['disclaimer']

    report_text = f"""
AI Health Assistant Report
==========================

Symptoms Entered:
{symptoms}

Possible Condition:
{possible_condition}

Why This May Match:
{reason}

Severity Level:
{severity}

Basic Care:
{basic_care}

When to See a Doctor:
{see_doctor_when}

Medical Disclaimer:
{disclaimer}
"""

    response = make_response(report_text)
    response.headers["Content-Type"] = "text/plain"
    response.headers["Content-Disposition"] = "attachment; filename=health_report.txt"
    return response

if __name__ == '__main__':
    app.run(debug=True)