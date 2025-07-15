from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

# Récupération des clés depuis les variables d'environnement
RINGOVER_API_KEY = os.getenv("RINGOVER_API_KEY")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

@app.route("/sms", methods=["POST"])
def send_confirmation_sms():
    try:
        data = request.get_json()
        print("✅ Données reçues :", data)

        # Extraction des champs
        phone = data.get("phone")
        firstname = data.get("firstname")
        meeting_time = data.get("meeting_time")
        password = data.get("password") or data.get("secret")
        from_alphanum = data.get("from_alphanum", "Nopillo")

        # Vérification du mot de passe
        if password != WEBHOOK_SECRET:
            print("❌ Mot de passe incorrect")
            return jsonify({"error": "Unauthorized"}), 401

        # Vérification des champs requis
        if not phone or not firstname or not meeting_time:
            print("❌ Champs manquants")
            return jsonify({"error": "Missing required fields"}), 400

        # Normalisation du numéro
        phone = phone.strip().replace(" ", "").replace("-", "")
        if phone.startswith("+33"):
            phone = "0" + phone[3:]
        if phone.startswith("0"):
            phone = "33" + phone[1:]

        # Capitalisation du prénom
        firstname = firstname.strip().capitalize()

        # Message personnalisé
        message = f"Bonjour {firstname}, votre RDV avec Nopillo est confirmé pour {meeting_time}. À très vite !"

        payload = {
            "to_number": phone,
            "text": message,
            "from_alias": from_alphanum
        }

        headers = {
            "Authorization": RINGOVER_API_KEY,
            "Content-Type": "application/json"
        }

        response = requests.post("https://public-api.ringover.com/v2/push/sms/v1", json=payload, headers=headers)

        print("📤 Message envoyé à Ringover. Payload :", payload)
        print("📥 Réponse Ringover :", response.status_code, response.text)

        if response.status_code != 200:
            return jsonify({"error": "Ringover API error", "details": response.text}), response.status_code

        return jsonify({"message": "SMS envoyé avec succès"}), 200

    except Exception as e:
        print("❌ Erreur interne :", str(e))
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
