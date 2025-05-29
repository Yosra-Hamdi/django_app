# project/soketi_client.py
import requests
import json
import os

def send_soketi_event(channel, event_name, data):
    soketi_host = os.getenv('PUSHER_HOST', 'localhost')
    soketi_port = os.getenv('PUSHER_PORT', '6001')
    app_id = os.getenv('PUSHER_APP_ID', 'mysoketiapp')
    secret = os.getenv('PUSHER_SECRET', 'mysoketisecret')

    url = f"http://{soketi_host}:{soketi_port}/apps/{app_id}/events"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {secret}"
    }
    payload = {
        "name": event_name,
        "channel": channel,
        "data": json.dumps(data)
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code != 200:
        raise Exception(f"Erreur lors de l'envoi de l'événement Soketi : {response.text}")
