from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

# Clés d’environnement
RINGOVER_API_KEY = os.getenv("RINGOVER_API_KEY")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

@app.route("/send_confirmation_sms", methods=["POST"])
def send_sms():
    try:
        print("✅ Requête reçue")
        data = request.get_json(force=True)
        print("📥 Données reçues :", data)

        phone = data.get("phone")
        firstname = data.get("firstname")
        meeting_time = data.get("meeting_time")
        password = data.get("password")
        from_alphanum = data.get("from_alphanum", "Nopillo")

        if password != WEBHOOK_SECRET:
            print("❌ Mot de passe invalide")
            return jsonify({"error": "Unauthorized"}), 401

        if not phone or not firstname or not meeting_time:
            print("❌ Champs manquants")
            return jsonify({"error": "Missing required fields"}), 400

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

        response = requests.post("https://public-api.ringover.com/v2/sms", json=payload, headers=headers)
        print("📤 Requête Ringover envoyée :", payload)
        print("📥 Réponse Ringover :", response.status_code, response.text)

        if response.status_code == 200:
            return jsonify({"success": True}), 200
        else:
            return jsonify({"error": "Ringover error", "details": response.text}), response.status_code

    except Exception as e:
        print("🔥 Erreur serveur :", str(e))
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

# Port dynamique pour Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
