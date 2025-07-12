from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)

@app.route('/')
def home():
    return "SMS confirmation webhook actif 🚀"

@app.route('/send_confirmation_sms', methods=['POST'])
def send_confirmation_sms():
    try:
        data = request.get_json()

        raw_phone = data.get('phone')
        firstname = data.get('firstname')
        meeting_time = data.get('meeting_time')
        secret = data.get('secret')
        from_alphanum = data.get('from_alphanum')

        print("Données reçues :", data)

        # Vérification du secret
        if secret != os.getenv("SECRET"):
            print("Erreur : secret invalide.")
            return jsonify({"error": "Unauthorized"}), 401

        # Nettoyage du numéro : supprime espaces, + et guillemets
        to_number = raw_phone.replace(" ", "").replace("+", "").replace('"', '')

        # Ajout de l'indicatif français si besoin
        if to_number.startswith("0"):
            to_number = "33" + to_number[1:]
        elif not to_number.startswith("33"):
            to_number = "33" + to_number

        # Création du message
        message = f"Bonjour {firstname}, votre RDV Nopillo est confirmé pour le {meeting_time}."

        print("Message formaté :", message)
        print("Numéro final :", to_number)

        # Envoi SMS via Ringover
        response = requests.post(
            "https://public-api.ringover.com/v2/sms",
            headers={
                "Authorization": f"Bearer {os.getenv('RINGOVER_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "to": to_number,
                "text": message,
                "from": from_alphanum
            }
        )

        print("Réponse Ringover :", response.status_code, response.text)

        if response.status_code == 200:
            return jsonify({"success": True}), 200
        else:
            return jsonify({"error": "Échec de l'envoi"}), 500

    except Exception as e:
        print("Erreur lors du traitement :", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
