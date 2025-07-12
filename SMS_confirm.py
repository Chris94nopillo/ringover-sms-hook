from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

RINGOVER_API_KEY = os.environ.get("RINGOVER_API_KEY")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")

@app.route('/send_confirmation_sms', methods=['POST'])
def send_confirmation_sms():
    try:
        data = request.get_json()

        # Vérifie le secret
        received_secret = data.get("secret")
        if received_secret != WEBHOOK_SECRET:
            return jsonify({"error": "Unauthorized"}), 401

        # Récupère et nettoie les données
        raw_phone = data.get("phone", "")
        firstname = data.get("firstname", "")
        meeting_time = data.get("meeting_time", "")
        from_alphanum = data.get("from_alphanum", "Nopillo")

        # Nettoyage du numéro : supprime espaces, + et guillemets
        to_number = raw_phone.replace(" ", "").replace("+", "").replace('"', '')

        # Préparation du message
        message = f"{firstname}, ton RDV Nopillo est confirmé le {meeting_time}. A bientôt !"

        # Envoie le SMS via l'API Ringover
        response = requests.post(
            "https://public-api.ringover.com/v2/sms",
            headers={"Authorization": f"Bearer {RINGOVER_API_KEY}"},
            json={
                "to_number": to_number,
                "text": message,
                "from": from_alphanum
            }
        )

        # Retourne la réponse de Ringover (ou erreur)
        if response.status_code == 200:
            return jsonify({"status": "SMS envoyé avec succès"}), 200
        else:
            return jsonify({
                "error": "Erreur lors de l'envoi du SMS",
                "ringover_response": response.text
            }), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=10000)
