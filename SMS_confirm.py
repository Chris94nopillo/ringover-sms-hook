from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

RINGOVER_API_URL = "https://public-api.ringover.com/v2/push/sms"
RINGOVER_API_KEY = os.environ.get("RINGOVER_API_KEY")  # plus sécurisé
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "nopillo2025SMS")

@app.route("/send_confirmation_sms", methods=["POST"])
def send_sms():
    data = request.json
    secret = data.get("secret")

    if secret != WEBHOOK_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    phone = data.get("phone")
    firstname = data.get("firstname")
    meeting_time = data.get("meeting_time")
    sender = data.get("from_alphanum", "Nopillo")

    if not phone or not firstname or not meeting_time:
        return jsonify({"error": "Missing parameters"}), 400

    # Format du message
    message = f"Bonjour {firstname}, votre RDV Nopillo est confirmé pour le {meeting_time}. Merci et à bientôt !"

    payload = {
        "from_alphanum": sender,
        "to_number": phone,
        "content": message
    }

    headers = {
        "Authorization": RINGOVER_API_KEY  # pas Bearer
    }

    response = requests.post(RINGOVER_API_URL, json=payload, headers=headers)

    if response.status_code == 200:
        return jsonify({"success": True}), 200
    else:
        return jsonify({"error": "Ringover API failed", "details": response.text}), 400

@app.route("/", methods=["GET"])
def health():
    return "OK", 200

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
