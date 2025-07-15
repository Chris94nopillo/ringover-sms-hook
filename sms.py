from flask import Flask, request, jsonify
import os
import re
import requests

app = Flask(__name__)

# Clés depuis les variables d’environnement
RINGOVER_API_KEY = os.getenv("RINGOVER_API_KEY")
WEBHOOK_SECRET   = os.getenv("WEBHOOK_SECRET")

@app.route("/sms", methods=["POST"])
def send_confirmation_sms():
    data = request.get_json(force=True)
    print("✅ Données reçues :", data)

    # — Extraction brute et cast en str pour éviter l'erreur .strip() sur int
    raw_phone     = str(data.get("phone", "")).strip()
    firstname_raw = str(data.get("firstname", "")).strip()
    raw_meeting   = data.get("meeting_time", "")
    # on caste toujours en str
    meeting_time  = str(raw_meeting).strip()
    password      = data.get("password") or data.get("secret")
    from_alphanum = data.get("from_alphanum", "Nopillo").strip()

    # Authent
    if password != WEBHOOK_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    # Champs obligatoires
    if not raw_phone or not firstname_raw or not meeting_time:
        return jsonify({"error": "Missing required fields"}), 400

    # Normalisation du numéro
    phone = re.sub(r"[^\d\+]", "", raw_phone)
    if phone.startswith("+"):
        phone = phone[1:]
    if phone.startswith("0"):
        phone = "33" + phone[1:]
    try:
        to_number = int(phone)
    except ValueError:
        return jsonify({"error": "Invalid phone number format"}), 400

    # Capitalisation du prénom
    firstname = firstname_raw.capitalize()

    # Construction du message
    message = f"Bonjour {firstname}, votre RDV est confirmé pour {meeting_time}. Merci et à bientôt !"

    # Préparation et envoi vers Ringover
    payload = {
        "from_alphanum": from_alphanum,
        "to_number"    : to_number,
        "content"      : message
    }
    headers = {
        "Authorization": RINGOVER_API_KEY,
        "Content-Type" : "application/json"
    }

    resp = requests.post(
        "https://public-api.ringover.com/v2/push/sms/v1",
        json=payload,
        headers=headers
    )
    print("📤 Payload envoyé :", payload)
    print("📥 Réponse Ringover :", resp.status_code, resp.text)

    if resp.status_code == 200:
        return jsonify({"success": True}), 200
    else:
        return jsonify({"error":"Ringover API error","details":resp.text}), resp.status_code

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
