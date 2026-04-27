import pandas as pd
import mysql.connector
import re

df = pd.read_excel("dataset.xlsx")

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
    "duit kutu": "data_theft",

    "virus": "malware",
    "malware": "malware",

    "spam": "spam",

    "attack": "cyber_attack",
    "serang": "cyber_attack",

    "maki": "cyberbullying",
    "cyberbuli": "cyberbullying",
    "buli": "cyberbullying",
    "kutuk": "cyberbullying",
    "hina": "cyberbullying",
    "bodoh": "cyberbullying",
    "hodoh": "cyberbullying",

    "sekat": "harassment",
    "link": "suspicious_link",
    "fraud": "fraud",
}

def clean(text):
    text = str(text).lower()
    return re.sub(r'[^\w\s]', '', text)

def detect(text):
    text = clean(text)

    for k, v in keyword_map.items():
        if k in text:
            return v, "threat"

    return "safe", "not_threat"

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Humaira1210.",
    database="cyber_threat_db"
)

cursor = conn.cursor()

for _, row in df.iterrows():
    post = row['post']
    label, status = detect(post)

    cursor.execute("""
        INSERT INTO detection_output (post, predicted_label, threat_status)
        VALUES (%s, %s, %s)
    """, (post, label, status))

conn.commit()
cursor.close()
conn.close()

print("✅ Data inserted successfully!")