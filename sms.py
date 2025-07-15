from flask import Flask, request, jsonify
import os
import re
import requests

app = Flask(__name__)

# Récupération des clés depuis les variables d'environnement
RINGOVER_API_KEY = os.getenv("RINGOVER_API_KEY")
WEBHOOK_SECRET   = os.getenv("WEBHOOK_SECRET")

@app.route("/sms", methods=["POST"])
def send_confirmation_sms():
    data = request.get_json(force=True)
    print("✅ Données reçues :", data)

    # Extraction des champs
    raw_phone    = data.get("phone", "")
    firstname    = data.get("firstname", "")
    meeting_time = data.get("meeting_time", "")
    secret       = data.get("password") or data.get("secret")
    from_alias   = data.get("from_alphanum", "Nopillo")

    # Vérification du secret
    if secret != WEBHOOK_SECRET:
        print("❌ Mot de passe incorrect")
        return jsonify({"error": "Unauthorized"}), 401

    # Vérification des champs obligatoires
    if not raw_phone or not firstname or not meeting_time:
        print("❌ Champs manquants")
        return jsonify({"error": "Missing required fields"}), 400

    # — Normalisation du numéro —
    # on retire tout sauf chiffres et +
    phone = re.sub(r"[^\d\+]", "", raw_phone)
    # on enlève le '+'
    if phone.startswith("+"):
        phone = phone[1:]
    # on transforme un '0XXXXXXXXX' en '33XXXXXXXXX'
    if phone.startswith("0"):
        phone = "33" + phone[1:]

    # — Mise en forme du prénom —
    firstname = firstname.strip().capitalize()

    # Construction du message
    message = (
        f"Bonjour {firstname}, votre RDV avec Nopillo "
        f"est confirmé pour {meeting_time}. À très vite !"
    )

    # Préparation de la requête vers Ringover
    payload = {
        "to_number": phone,
        "text":      message,
        "from_alias": from_alias
    }
    headers = {
        "Authorization": RINGOVER_API_KEY,
        "Content-Type":  "application/json"
    }

    # Envoi
    resp = requests.post(
        "https://public-api.ringover.com/v2/push/sms/v1",
        json=payload, headers=headers
    )
    print("📤 Payload Ringover:", payload)
    print("📥 Réponse Ringover:", resp.status_code, resp.text)

    if resp.status_code != 200:
        return jsonify({
            "error":   "Ringover API error",
            "details": resp.text
        }), resp.status_code

    # Tout est OK
    return jsonify({"success": True}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
