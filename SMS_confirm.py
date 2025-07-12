from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

# Lecture des variables d'environnement
RINGOVER_API_KEY = os.getenv("RINGOVER_API_KEY")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

@app.route("/send_confirmation_sms", methods=["POST"])
def send_confirmation_sms():
    try:
        print("✅ Requête reçue sur /send_confirmation_sms")

        data = request.get_json()
        print("📥 Données JSON reçues :", data)

        # Sécurité : mot de passe
        password = data.get("password") or data.get("secret")
        if password != WEBHOOK_SECRET:
            print("❌ Mot de passe incorrect :", password)
            return jsonify({"error": "Unauthorized"}), 401

        # Extraction des champs
        phone = data.get("phone")
        firstname = data.get("firstname")
        meeting_time = data.get("meeting_time")
        from_alphanum = data.get("from_alphanum", "Nopillo")

        # Vérification des champs
        if not all([phone, firstname, meeting_time]):
            print("❌ Champs manquants :", {"phone": phone, "firstname": firstname, "meeting_time": meeting_time})
            return jsonify({"error": "Missing required fields"}), 400

        # Message SMS
        message = f"Bonjour {firstname}, votre RDV est confirmé pour {meeting_time}. À très vite !"
        payload = {
            "number": phone,
            "text": message,
            "from": from_alphanum
        }
        headers = {
            "Authorization": RINGOVER_API_KEY,
            "Content-Type": "application/json"
        }

        print("📤 Envoi du SMS à Ringover...")
        print("➡️ Payload :", payload)
        print("➡️ Headers :", headers)

        response = requests.post("https://public-api.ringover.com/v2/sms", json=payload, headers=headers)

        print("📬 Réponse Ringover :", response.status_code, response.text)

        if response.status_code == 200:
            return jsonify({"success": True, "details": response.json()}), 200
        else:
            return jsonify({"error": "Ringover API error", "details": response.text}), response.status_code

    except Exception as e:
        print("🔥 Erreur inattendue :", str(e))
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

# Lancement de l'app compatible Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(debug=False, host="0.0.0.0", port=port)
