import os
from mailjet_rest import Client

def send_password_reset_email(to_email, reset_link):
    # Initialiser le client Mailjet
    mailjet = Client(auth=(os.getenv('MAILJET_API_KEY'), os.getenv('MAILJET_API_SECRET')), version='v3.1')

    # Préparer les données de l'email
    subject = "Réinitialisation de votre mot de passe"
    text_content = f"Cliquez sur ce lien pour réinitialiser votre mot de passe : {reset_link}"
    html_content = f"""
    <h1>Réinitialisation de votre mot de passe</h1>
    <p>Cliquez sur le lien suivant pour réinitialiser votre mot de passe :</p>
    <a href="{reset_link}">{reset_link}</a>
    """

    data = {
        'Messages': [
            {
                "From": {
                    "Email": "hamdyyosra010@gmail.com",  # Remplacez par votre adresse email
                    "Name": "hello_business",  # Remplacez par le nom de votre application
                },
                "To": [
                    {
                        "Email": "hamdiyosra010@gmail.com",
                        "Name": "yosra",  # Remplacez par le nom de l'utilisateur si disponible
                    }
                ],
                "Subject": subject,
                "TextPart": text_content,
                "HTMLPart": html_content,
            }
        ]
    }

    # Envoyer l'email
    result = mailjet.send.create(data=data)
    if result.status_code == 200:
        print("Email de réinitialisation envoyé avec succès !")
        return True
    else:
        print(f"Erreur lors de l'envoi de l'email : {result.status_code}")
        print(result.json())
        return False