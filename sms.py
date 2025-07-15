from flask import Flask, request, jsonify
import os
import re
import requests
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

# Récupération des clés depuis les variables d'environnement
RINGOVER_API_KEY = os.getenv("RINGOVER_API_KEY")
WEBHOOK_SECRET   = os.getenv("WEBHOOK_SECRET")

# Mois en français
FRENCH_MONTHS = {
    1: "janvier",   2: "février", 3: "mars",
    4: "avril",     5: "mai",     6: "juin",
    7: "juillet",   8: "août",    9: "septembre",
    10:"octobre",  11: "novembre",12: "décembre"
}

@app.route("/sms", methods=["POST"])
def send_confirmation_sms():
    data = request.get_json(force=True)
    print("✅ Données reçues :", data)

    # → Extraction brute
    raw_phone    = str(data.get("phone", "")).strip()
    firstname_raw= str(data.get("firstname", "")).strip()
    raw_meeting  = data.get("meeting_time", "")
    password     = data.get("password") or data.get("secret")
    from_alias   = data.get("from_alphanum", "Nopillo").strip()

    # Authentification
    if password != WEBHOOK_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    # Champs obligatoires
    if not raw_phone or not firstname_raw or raw_meeting is None:
        return jsonify({"error": "Missing required fields"}), 400

    # — Normalisation du numéro FR → 33XXXXXXXXX
    phone = re.sub(r"[^\d\+]", "", raw_phone)
    if phone.startswith("+"):
        phone = phone[1:]
    if phone.startswith("0"):
        phone = "33" + phone[1:]
    try:
        to_number = int(phone)
    except ValueError:
        return jsonify({"error": "Invalid phone number format"}), 400

    # — Capitalisation du prénom
    firstname = firstname_raw.capitalize()

    # — Formatage de la date/heure
    meeting_time = ""
    if isinstance(raw_meeting, (int, float)) or (isinstance(raw_meeting, str) and raw_meeting.isdigit()):
        # epoch ms → datetime UTC
        ms = int(raw_meeting)
        dt_utc = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
        # Europe/Paris (UTC+2 en été)
        dt_local = dt_utc.astimezone(timezone(timedelta(hours=2)))
        day   = dt_local.day
        month = FRENCH_MONTHS[dt_local.month]
        year  = dt_local.year
        hour  = dt_local.hour
        minute= dt_local.minute
        meeting_time = f"{day} {month} {year} à {hour}h{minute:02d}"
    else:
        # on garde la chaîne telle quelle (ex: "18 juillet à 12h15")
        meeting_time = str(raw_meeting).strip()

    # — Construction du message
    message = (
        f"Bonjour {firstname}, votre RDV avec Nopillo "
        f"est confirmé pour {meeting_time}. À très vite !"
    )

    # → Payload pour Ringover
    payload = {
        "from_alphanum": from_alias,
        "to_number"    : to_number,
        "content"      : message
    }
    headers = {
        "Authorization": RINGOVER_API_KEY,
        "Content-Type" : "application/json"
    }

    resp = requests.post(
        "https://public-api.ringover.com/v2/push/sms/v1",
        json=payload, headers=headers
    )
    print("📤 Payload envoyé :", payload)
    print("📥 Réponse Ringover :", resp.status_code, resp.text)

    if resp.status_code == 200:
        return jsonify({"success": True}), 200
    else:
        return jsonify({
            "error":   "Ringover API error",
            "details": resp.text
        }), resp.status_code

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
