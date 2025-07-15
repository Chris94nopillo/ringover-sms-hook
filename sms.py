from flask import Flask, request, jsonify
import os
import requests
import re

app = Flask(__name__)

# Récupération des clés depuis les variables d'environnement
RINGOVER_API_KEY = os.getenv("RINGOVER_API_KEY")
WEBHOOK_SECRET   = os.getenv("WEBHOOK_SECRET")

@app.route("/sms", methods=["POST"])
def send_confirmation_sms():
    data = request.get_json(force=True)
    print("✅ Données reçues :", data)

    # Extraction & nettoyage des champs
    raw_phone     = str(data.get("phone", "")).strip()
    firstname_raw = data.get("firstname", "").strip()
    meeting_time  = data.get("meeting_time", "").strip()
    password      = data.get("password") or data.get("secret")
    from_alphanum = data.get("from_alphanum", "Nopillo").strip()

    # Vérification du secret
    if password != WEBHOOK_SECRET:
        print("❌ Mot de passe incorrect")
        return jsonify({"error": "Unauthorized"}), 401

    # Vérification des champs obligatoires
    if not raw_phone or not firstname_raw or not meeting_time:
        print("❌ Champs manquants")
        return jsonify({"error": "Missing required fields"}), 400

    # Normalisation du numéro : on retire tout sauf les chiffres et le '+'
    phone = re.sub(r"[^\d\+]", "", raw_phone)
    if phone.startswith("+"):
        phone = phone[1:]
    if phone.startswith("0"):
        phone = "33" + phone[1:]

    # Conversion en entier, comme attendu par l'API Ringover
    try:
        to_number = int(phone)
    except ValueError:
        print("❌ Numéro invalide après nettoyage :", phone)
        return jsonify({"error": "Invalid phone number format"}), 400

    # Capitalisation du prénom
    firstname = firstname_raw.capitalize()

    # Construction du message
    message = (
        f"Bonjour {firstname}, votre RDV est confirmé pour {meeting_time}. "
        "À très vite !"
    )

    # Préparation du payload pour Ringover
    payload = {
        "from_alphanum": from_alphanum,
        "to_number":     to_number,
        "content":       message
    }
    headers = {
        "Authorization": RINGOVER_API_KEY,
        "Content-Type":  "application/json"
    }

    # Envoi vers l'API Ringover
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
        return jsonify({
            "error":   "Ringover API error",
            "details": resp.text
        }), resp.status_code

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
