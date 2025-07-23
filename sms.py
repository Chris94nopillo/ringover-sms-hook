from flask import Flask, request, jsonify
import os
import re
import requests
import uuid
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

# Clés depuis les variables d'environnement
RINGOVER_API_KEY = os.getenv("RINGOVER_API_KEY")
WEBHOOK_SECRET   = os.getenv("WEBHOOK_SECRET")

# Mois en français pour le formatage
FRENCH_MONTHS = {
    1: "janvier", 2: "février", 3: "mars",
    4: "avril",   5: "mai",      6: "juin",
    7: "juillet", 8: "août",     9: "septembre",
    10:"octobre", 11:"novembre",12:"décembre"
}

@app.route("/sms", methods=["POST"])
def send_confirmation_sms():
    # Génération d'un ID court et timestamp pour le log
    req_id = uuid.uuid4().hex[:8]
    ts     = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

    # Lecture du body brut et des headers
    raw_body = request.get_data(as_text=True)
    headers  = dict(request.headers)

    # Logging granulaire
    print(f"[{ts}] [{req_id}] → RAW BODY   : {raw_body}")
    print(f"[{ts}] [{req_id}] → HEADERS    : {headers}")

    # Tentative de parsing JSON
    try:
        data = request.get_json(force=True)
        print(f"[{ts}] [{req_id}] → PARSED JSON: {data}")
    except Exception as e:
        print(f"[{ts}] [{req_id}] ⚠️ JSON parse error: {e}")
        return jsonify({"error": "Invalid JSON"}), 400

    # Extraction des champs
    raw_phone     = str(data.get("phone", "")).strip()
    firstname_raw = str(data.get("firstname", "")).strip()
    raw_meeting   = data.get("meeting_time", "")
    reminder      = data.get("reminder", False)
    password      = data.get("password") or data.get("secret")
    from_alias    = data.get("from_alphanum", "Nopillo").strip()

    # Authentification
    if password != WEBHOOK_SECRET:
        print(f"[{ts}] [{req_id}] ❌ Secret invalid: {password}")
        return jsonify({"error": "Unauthorized"}), 401

    # Vérification des champs obligatoires
    if not raw_phone or not firstname_raw or raw_meeting is None:
        print(f"[{ts}] [{req_id}] ❌ Missing required fields")
        return jsonify({"error": "Missing required fields"}), 400

    # Normalisation du numéro (33XXXXXXXXX)
    phone = re.sub(r"[^\d\+]", "", raw_phone)
    if phone.startswith("+"):
        phone = phone[1:]
    if phone.startswith("0"):
        phone = "33" + phone[1:]
    try:
        to_number = int(phone)
    except ValueError:
        print(f"[{ts}] [{req_id}] ❌ Invalid phone after normalization: {phone}")
        return jsonify({"error": "Invalid phone number format"}), 400

    # Capitalisation du prénom
    firstname = firstname_raw.capitalize()

    # Formatage de la date/heure
    if isinstance(raw_meeting, (int, float)) or (isinstance(raw_meeting, str) and raw_meeting.isdigit()):
        ms     = int(raw_meeting)
        dt_utc = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
        dt_loc = dt_utc.astimezone(timezone(timedelta(hours=2)))  # Europe/Paris été
        meeting_time = f"{dt_loc.day} {FRENCH_MONTHS[dt_loc.month]} {dt_loc.year} à {dt_loc.hour}h{dt_loc.minute:02d}"
    else:
        meeting_time = str(raw_meeting).strip()

    # Construction du message
    if reminder:
        message = (
            f"Bonjour {firstname}, petit rappel de votre RDV avec Nopillo prévu aujourd'hui "
            f"{meeting_time}. À tout à l’heure !"
        )
    else:
        message = (
            f"Bonjour {firstname}, votre RDV avec Nopillo est confirmé pour le "
            f"{meeting_time}. À très vite !"
        )

    # Préparation du payload Ringover
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
    print(f"[{ts}] [{req_id}] 📤 Payload sent: {payload}")
    print(f"[{ts}] [{req_id}] 📥 Ringover response: {resp.status_code} {resp.text}")

    if resp.status_code == 200:
        return jsonify({"success": True}), 200
    else:
        print(f"[{ts}] [{req_id}] ❌ Ringover API error")
        return jsonify({"error": "Ringover API error", "details": resp.text}), resp.status_code

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
