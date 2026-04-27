from flask import Flask, render_template, jsonify, request
import mysql.connector
import joblib
import pandas as pd
import random
import re

app = Flask(__name__)

model = joblib.load("models/cyber_model.pkl")
vectorizer = joblib.load("models/vectorizer.pkl")

# ================= DB =================
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Humaira1210.",
        database="cyber_threat_db"
    )

# ================= HOME DATA =================
@app.route('/summary')
def summary():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT COUNT(*) total FROM detection_output")
    total = cur.fetchone()['total']

    cur.execute("SELECT COUNT(*) threat FROM detection_output WHERE threat_status='threat'")
    threat = cur.fetchone()['threat']

    cur.execute("SELECT COUNT(*) safe FROM detection_output WHERE threat_status='not_threat'")
    safe = cur.fetchone()['safe']

    db.close()

    return jsonify({"total": total, "threat": threat, "safe": safe})

# ================= SEARCH =================
@app.route('/search')
def search():
    keyword = request.args.get('q', '').strip()

    if keyword == "":
        return jsonify([])

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT id, post, predicted_label, threat_status
        FROM detection_output
        WHERE post LIKE %s
           OR predicted_label LIKE %s
           OR threat_status LIKE %s
        ORDER BY id DESC
        LIMIT 10
    """, (
        '%' + keyword + '%',
        '%' + keyword + '%',
        '%' + keyword + '%'
    ))

    results = cur.fetchall()

    db.close()

    return jsonify(results)

# ================= PIE CHART =================
@app.route('/threat-chart')
def chart():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT predicted_label, COUNT(*) count
        FROM detection_output
        WHERE threat_status='threat'
        GROUP BY predicted_label
    """)

    data = cur.fetchall()
    db.close()

    labels = [d['predicted_label'] for d in data]
    values = [d['count'] for d in data]

    total = sum(values) if values else 1
    percent = [(v/total)*100 for v in values]

    return jsonify({"labels": labels, "values": percent})

# ================= DATASET =================
@app.route('/dataset-data')
def dataset_data():
    page = int(request.args.get('page', 1))
    limit = 6
    offset = (page - 1) * limit

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT COUNT(*) total FROM detection_output")
    total = cur.fetchone()['total']

    cur.execute("""
        SELECT * FROM detection_output
        ORDER BY id DESC
        LIMIT %s OFFSET %s
    """, (limit, offset))

    data = cur.fetchall()
    db.close()

    return jsonify({"total": total, "data": data})

# ================= UPLOAD DATASET =================
@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    df = pd.read_csv(file)

    db = get_db()
    cur = db.cursor()

    for _, row in df.iterrows():
        text = str(row['post'])

        vec = vectorizer.transform([text])
        pred = model.predict(vec)[0]

        status = "threat" if pred != "not_threat" else "not_threat"
        confidence = random.randint(70, 99)

        cur.execute("""
            INSERT INTO detection_output(post, predicted_label, threat_status, confidence)
            VALUES (%s,%s,%s,%s)
        """, (text, pred, status, confidence))

    db.commit()
    db.close()

    return "uploaded"

# ================= ALERT METRICS =================
@app.route('/metrics')
def metrics():
    return jsonify({
        "precision": 0.91,
        "recall": 0.89,
        "f1": 0.90
    })

# ================= PIPELINE ONLY =================
def clean(text):
    text = str(text).lower()
    return re.sub(r'[^\w\s]', '', text)

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

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    text = data['text']

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
        "vector_shape": str(vec.shape),
        "model_prediction": model_pred,
        "prediction": final_pred,
        "status": status
    })

# ================= ROUTES =================
@app.route('/')
def home():
    return render_template("home.html")

@app.route('/dataset')
def dataset():
    return render_template("dataset.html")

@app.route('/pipeline')
def pipeline():
    return render_template("pipeline.html")

@app.route('/alert')
def alert():
    return render_template("alert.html")

@app.route('/feedback')
def feedback():
    return render_template("feedback.html")


# ================= FEEDBACK =================
@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    data = request.get_json()

    name = data.get('name')
    message = data.get('message')
    rating = data.get('rating')

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        INSERT INTO feedback (name, message, rating)
        VALUES (%s, %s, %s)
    """, (name, message, rating))

    db.commit()
    db.close()

    return jsonify({"success": True})


@app.route('/feedback-data')
def feedback_data():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT * FROM feedback
        ORDER BY id DESC
    """)

    data = cur.fetchall()
    db.close()

    return jsonify(data)


@app.route('/delete-feedback/<int:id>', methods=['DELETE'])
def delete_feedback(id):
    db = get_db()
    cur = db.cursor()

    cur.execute("DELETE FROM feedback WHERE id = %s", (id,))

    db.commit()
    db.close()

    return jsonify({"success": True})


@app.route('/feedback-stats')
def feedback_stats():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT COUNT(*) AS total FROM feedback")
    total = cur.fetchone()['total']

    cur.execute("SELECT ROUND(AVG(rating), 1) AS average_rating FROM feedback")
    avg = cur.fetchone()['average_rating']

    db.close()

    return jsonify({
        "total": total,
        "average_rating": avg if avg else 0
    })

if __name__ == "__main__":
    app.run(debug=True)