from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import re
import os

app = Flask(__name__)
CORS(app)

model = joblib.load("models/cyber_model.pkl")
vectorizer = joblib.load("models/vectorizer.pkl")

keyword_map = {
    "hack": "hacking",
    "godam": "hacking",
    "scam": "scam",
    "phishing": "scam",
    "link pishing": "scam",
    "curi": "data_theft",
    "akaun": "data_theft",
    "password": "data_theft",
    "otp": "data_theft",
    "tac": "data_theft",
    "virus": "malware",
    "malware": "malware",
    "spam": "spam",
    "attack": "cyber_attack",
    "serang": "cyber_attack",
    "sekat": "harassment",
    "maki": "cyberbullying",
    "buli": "cyberbullying",
    "kutuk": "cyberbullying",
    "bodoh": "cyberbullying",
    "link": "suspicious_link",
    "fraud": "fraud"
}

def clean(text):
    text = str(text).lower()
    return re.sub(r"[^\w\s]", "", text)

@app.route("/")
def home():
    return jsonify({
        "message": "Malay Cyber Threat Detection API is running",
        "endpoint": "/predict",
        "method": "POST"
    })

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    text = data.get("text", "")

    cleaned = clean(text)

    keywords_found = []
    category_score = {}

    for keyword, category in keyword_map.items():
        if keyword in cleaned:
            keywords_found.append(keyword)
            category_score[category] = category_score.get(category, 0) + 1

    vec = vectorizer.transform([cleaned])
    model_pred = model.predict(vec)[0]

    if category_score:
        final_pred = max(category_score, key=category_score.get)
        status = "threat"
    else:
        final_pred = model_pred
        status = "threat" if final_pred != "not_threat" else "not_threat"

    return jsonify({
        "input": text,
        "cleaned": cleaned,
        "keywords": keywords_found,
        "model_prediction": model_pred,
        "prediction": final_pred,
        "status": status
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)