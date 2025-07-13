from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

RINGOVER_API_KEY = os.getenv("RINGOVER_API_KEY")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

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

    # Chiffres obligatoires
    phone = data.get("phone")
    firstname = data.get("firstname")
    meeting_time = data.get("meeting_time")
    if not phone or not firstname or not meeting_time:
        return jsonify({"error": "Missing required fields"}), 400

    # Préparation du SMS pour Ringover
    message = f"Bonjour {firstname}, votre RDV est confirmé pour {meeting_time}."
    payload = {
        "from_alphanum": data.get("from_alphanum", "Nopillo"),
        "to_number": int(phone),
        "content": message
    }
    headers = {
        "Authorization": RINGOVER_API_KEY,
        "Content-Type": "application/json"
    }

    # Envoi vers Ringover — URL corrigée
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
    app.run(host="0.0.0.0", port=port)
