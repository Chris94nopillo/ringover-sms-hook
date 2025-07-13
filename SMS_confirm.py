from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

# Lecture des variables d'environnement
RINGOVER_API_KEY = os.getenv("RINGOVER_API_KEY")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

@app.route('/send_confirmation_sms', methods=['POST'])
def send_confirmation_sms():
    try:
        data = request.get_json()

        # Debug - afficher les données reçues
        print("✅ Données reçues :", data)

        # Champs extraits
        phone = data.get("phone")
        firstname = data.get("firstname")
        meeting_time = data.get("meeting_time")
        password = data.get("password") or data.get("secret")
        from_alphanum = data.get("from_alphanum", "Nopillo")

        # Sécurité : vérification du mot de passe
        if password != WEBHOOK_SECRET:
            print("❌ Mot de passe incorrect")
            return jsonify({"error": "Unauthorized"}), 401

        # Validation des champs requis
        if not phone or not firstname or not meeting_time:
            print("❌ Champs manquants")
            return jsonify({"error": "Missing required fields"}), 400

        # Message personnalisé
        message = f"Bonjour {firstname}, votre RDV est confirmé pour {meeting_time}. À très vite !"

        # Requête vers Ringover
        payload = {
            "number": phone,
            "text": message,
            "from": from_alphanum
        }

        headers = {
            "Authorization": RINGOVER_API_KEY,
            "Content-Type": "application/json"
        }

        response = requests.post("https://public-api.ringover.com/v2/sms", json=payload, headers=headers)

        # Debug
        print("📤 Requête envoyée à Ringover :", payload)
        print("📥 Réponse Ringover :", response.status_code, response.text)

        if response.status_code == 200:
            return jsonify({"success": True, "details": response.json()}), 200
        else:
            return jsonify({"error": "Ringover API error", "details": response.text}), response.status_code

    except Exception as e:
        print("🔥 Erreur inattendue :", str(e))
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

# Lancement local et pour Render (port explicite)
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
