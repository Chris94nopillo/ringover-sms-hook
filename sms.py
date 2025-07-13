from flask import Flask, request, jsonify
import os
import requests
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

RINGOVER_API_KEY = os.getenv("RINGOVER_API_KEY")
WEBHOOK_SECRET   = os.getenv("WEBHOOK_SECRET")

# Table des mois en français
FRENCH_MONTHS = {
    1:  "janvier",   2:  "février", 3:  "mars",
    4:  "avril",     5:  "mai",     6:  "juin",
    7:  "juillet",   8:  "août",    9:  "septembre",
    10: "octobre",   11: "novembre",12: "décembre"
}

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

    if not phone or not firstname or not meeting_time:
        return jsonify({"error": "Missing required fields"}), 400

    # Si meeting_time est un timestamp en ms, on convertit en Europe/Paris
    human_time = meeting_time
    if isinstance(meeting_time, (int, float)) or (isinstance(meeting_time, str) and meeting_time.isdigit()):
        ms = int(meeting_time)
        # UTC -> datetime
        dt_utc = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
        # Conversion en Europe/Paris (UTC+2 en été)
        dt_local = dt_utc.astimezone(tz=timezone(timedelta(hours=2)))
        day   = dt_local.day
        month = FRENCH_MONTHS[dt_local.month]
        year  = dt_local.year
        hour  = dt_local.hour
        minute= dt_local.minute
        human_time = f"{day} {month} {year} à {hour}h{minute:02d}"

    # Construction du message
    message = f"Bonjour {firstname}, votre rendez-vous avec Nopillo est confirmé pour {human_time}. À bientôt !"

    payload = {
        "from_alphanum": sender,
        "to_number":     int(phone),
        "content":       message
    }
    headers = {
        "Authorization": RINGOVER_API_KEY,
        "Content-Type":  "application/json"
    }

    # Envoi vers Ringover
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
