import os
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)

RINGOVER_API_KEY = os.getenv("RINGOVER_API_KEY")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

@app.route('/')
def home():
    return 'Webhook Ringover is up!'

@app.route('/send_confirmation_sms', methods=['POST'])
def send_confirmation_sms():
    try:
        print("📥 Réception d'une requête POST sur /send_confirmation_sms")

        data = request.get_json()
        print("🧾 Payload brut reçu :", data)

        # Vérification du mot de passe
        password = data.get("password")
        print(f"🔐 Mot de passe reçu : {password}")

        if password != WEBHOOK_SECRET:
            print("⛔ Mot de passe incorrect.")
            return jsonify({"error": "Unauthorized"}), 401

        # Extraction des données
        prenom = data.get("firstname", "")
        date_heure = data.get("datetime", "")
        numero = data.get("phone", "")

        print(f"📤 Données extraites : prénom = {prenom}, date = {date_heure}, numéro = {numero}")

        if not all([prenom, date_heure, numero]):
            print("⚠️ Champs manquants.")
            return jsonify({"error": "Missing required fields"}), 400

        # Message à envoyer
        message = f"Bonjour {prenom}, votre RDV est bien confirmé pour le {date_heure}. À très vite, l’équipe Nopillo."
        print(f"✉️ Message préparé : {message}")

        # Requête vers l’API Ringover
        response = requests.post(
            "https://public-api.ringover.com/v2/sms",
            headers={
                "Authorization": f"Bearer {RINGOVER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "number": numero,
                "text": message
            }
        )

        print("📡 Requête envoyée à Ringover. Code retour :", response.status_code)
        print("🧾 Réponse Ringover :", response.text)

        if response.status_code != 200:
            print("❌ Échec de l'envoi du SMS.")
            return jsonify({"error": "SMS sending failed", "details": response.text}), 500

        print("✅ SMS envoyé avec succès !")
        return jsonify({"status": "success", "message": "SMS sent"}), 200

    except Exception as e:
        print("🔥 Erreur serveur :", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
