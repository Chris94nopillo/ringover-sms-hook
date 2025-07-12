import os
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route("/")
def index():
    return "✅ Webhook Ringover-SMS prêt à l'emploi !"

@app.route("/send_confirmation_sms", methods=["POST"])
def send_confirmation_sms():
    try:
        data = request.get_json()
        print("📥 Données reçues :", data)

        # Vérification du secret
        if data.get("secret") != os.environ.get("WEBHOOK_SECRET"):
            print("❌ Secret invalide")
            return jsonify({"error": "Unauthorized"}), 403

        # Extraction et nettoyage des données
        raw_phone = data.get("phone", "")
        firstname = data.get("firstname", "")
        meeting_time = data.get("meeting_time", "")
        from_alphanum = data.get("from_alphanum", "Nopillo")

        # Nettoyage du numéro : supprime espaces, + et guillemets
        to_number = raw_phone.replace(" ", "").replace("+", "").replace('"', '')
        if not to_number.startswith("33"):
            to_number = "33" + to_number.lstrip("0")  # ex : 0612... => 33612...

        # Construction du message
        message = f"👋 Bonjour {firstname}, merci pour votre intérêt ! Votre rendez-vous est bien confirmé pour le {meeting_time}. À très vite ! L’équipe Nopillo."

        print("📤 Envoi du SMS à :", to_number)
        print("📝 Message :", message)

        # Envoi de la requête POST vers l'API Ringover
        response = requests.post(
            "https://public-api.ringover.com/v2/sms",
            json={
                "number": to_number,
                "message": message,
                "from": from_alphanum,
            },
            headers={
                "Authorization": f"Bearer {os.environ.get('RINGOVER_API_KEY')}"
            },
        )

        print("✅ Statut Ringover :", response.status_code)
        print("📦 Réponse Ringover :", response.text)

        return jsonify({"status": "SMS envoyé"}), 200

    except Exception as e:
        print("🔥 Erreur détectée :", str(e))
        return jsonify({"error": "Erreur interne", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
