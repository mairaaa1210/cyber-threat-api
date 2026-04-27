import pandas as pd
import joblib
import re
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

df = pd.read_excel("data/dataset.xlsx").dropna()

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
    "link": "suspicious_link",
    "fraud": "fraud"
}

def clean(text):
    text = str(text).lower()
    return re.sub(r'[^\w\s]', '', text)

def auto_label(text):
    text = clean(text)
    score = {}

    for k, v in keyword_map.items():
        if k in text:
            score[v] = score.get(v, 0) + 1

    return max(score, key=score.get) if score else "not_threat"

df["label"] = df["post"].apply(auto_label)

X = df["post"]
y = df["label"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

vectorizer = TfidfVectorizer(max_features=5000)
X_train_vec = vectorizer.fit_transform(X_train)

model = MultinomialNB()
model.fit(X_train_vec, y_train)

joblib.dump(model, "models/cyber_model.pkl")
joblib.dump(vectorizer, "models/vectorizer.pkl")

print("✅ Training completed")