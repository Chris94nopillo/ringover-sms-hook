from flask import Flask, request, jsonify
import os
import re
import requests
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

# Récupération des clés depuis les variables d'environnement
RINGOVER_API_KEY = os.getenv("RINGOVER_API_KEY")
WEBHOOK_SECRET   = os.getenv("WEBHOOK_SECRET")

# Mois en français pour le formatage de date
FRENCH_MONTHS = {
    1: "janvier",   2: "février", 3: "mars",
    4: "avril",     5: "mai",     6: "juin",
    7: "juillet",   8: "août",    9: "septembre",
    10: "octobre", 11: "novembre", 12: "décembre"
}

@app.route("/sms", methods=["POST"])
def send_confirmation_sms():
    data = request.get_json(force=True)
    print("✅ Données reçues :", data)

    # Extraction et nettoyage
    raw_phone     = str(data.get("phone", "")).strip()
    firstname_raw = str(data.get("firstname", "")).strip()
    raw_meeting   = data.get("meeting_time", "")
    reminder      = data.get("reminder", False)
    password      = data.get("password") or data.get("secret")
    from_alias    = data.get("from_alphanum", "Nopillo").strip()

    # Authentification
    if password != WEBHOOK_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    # Champs obligatoires
    if not raw_phone or not firstname_raw or raw_meeting is None:
        return jsonify({"error": "Missing required fields"}), 400

    # Normalisation du numéro en 33XXXXXXXXX
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

    # Formatage de la date/heure
    if isinstance(raw_meeting, (int, float)) or (isinstance(raw_meeting, str) and raw_meeting.isdigit()):
        ms      = int(raw_meeting)
        dt_utc  = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
        dt_loc  = dt_utc.astimezone(timezone(timedelta(hours=2)))
        day     = dt_loc.day
        month   = FRENCH_MONTHS[dt_loc.month]
        year    = dt_loc.year
        hour    = dt_loc.hour
        minute  = dt_loc.minute
        meeting_time = f"{day} {month} {year} à {hour}h{minute:02d}"
    else:
        meeting_time = str(raw_meeting).strip()

    # Choix du message selon confirmation ou rappel
    if reminder:
        # Rappel le jour même à 8h45 (la logique de timing est gérée dans HubSpot)
        message = (
            f"Bonjour {firstname}, rappel de votre RDV avec Nopillo prévu aujourd'hui le "
            f"{meeting_time}. À tout à l’heure !"
        )
    else:
        # Message de confirmation initiale
        message = (
            f"Bonjour {firstname}, votre RDV avec Nopillo est confirmé pour le "
            f"{meeting_time}. À très vite !"
        )

    # Préparation du payload pour l’API Ringover
    payload = {
        "from_alphanum": from_alias,
        "to_number"    : to_number,
        "content"      : message
    }
    headers = {
        "Authorization": RINGOVER_API_KEY,
        "Content-Type" : "application/json"
    }

    # Envoi vers Ringover
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
