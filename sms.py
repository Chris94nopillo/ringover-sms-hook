from flask import Flask, request, jsonify
import os
import requests
from datetime import datetime

app = Flask(__name__)

RINGOVER_API_KEY = os.getenv("RINGOVER_API_KEY")
WEBHOOK_SECRET   = os.getenv("WEBHOOK_SECRET")

@app.route('/', methods=['GET'])
def index():
    return "API is running", 200

@app.route('/sms', methods=['POST'])
def send_confirmation_sms():
    data = request.get_json()
    print("✅ Données reçues :", data)

    # Vérification du secret
    pwd = data.get("password") or data.get("secret")
    if pwd != WEBHOOK_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    # Extraction des champs
    phone        = data.get("phone")
    firstname    = data.get("firstname")
    meeting_time = data.get("meeting_time")
    sender       = data.get("from_alphanum", "Nopillo")

    # Validation minimale
    if not phone or not firstname or not meeting_time:
        return jsonify({"error": "Missing required fields"}), 400

    # ——————————————
    # Conversion du timestamp si nécessaire
    human_time = meeting_time
    # Détecte une chaîne de chiffres (epoch en ms)
    if isinstance(meeting_time, (int, float)) or (isinstance(meeting_time, str) and meeting_time.isdigit()):
        ms = int(meeting_time)
        # convertit en seconde
        dt = datetime.fromtimestamp(ms / 1000)
        human_time = dt.strftime("%d %B %Y à %Hh%M")  # ex: "15 juillet 2025 à 09h45"
    # ——————————————

    # Construction du message
    message = f"Bonjour {firstname}, votre RDV est confirmé pour {human_time}. À bientôt !"

    payload = {
        "from_alphanum": sender,
        "to_number":     int(phone),
        "content":       message
    }
    headers = {
        "Authorization": RINGOVER_API_KEY,
        "Content-Type":  "application/json"
    }

    # Appel à l’API Ringover (URL v1)
    resp = requests.post(
        "https://public-api.ringover.com/v2/push/sms/v1",
        json=payload, headers=headers
    )
    print("📥 Ringover response:", resp.status_code, resp.text)

    if resp.ok:
        return jsonify({"success": True}), 200
    else:
        return jsonify({"error": "Ringover API error", "details": resp.text}), resp.status_code

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
