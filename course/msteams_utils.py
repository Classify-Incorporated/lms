import requests
from django.conf import settings
from msal import ConfidentialClientApplication

def get_access_token():
    app = ConfidentialClientApplication(
        client_id=settings.MS_CLIENT_ID,
        client_credential=settings.MS_CLIENT_SECRET,
        authority=f"https://login.microsoftonline.com/{settings.MS_TENANT_ID}"
    )
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if 'access_token' in result:
        return result['access_token']
    else:
        raise Exception(f"Error acquiring access token: {result.get('error_description', 'Unknown error')}")


def get_user_id(email):
    access_token = get_access_token()
    user_url = f"https://graph.microsoft.com/v1.0/users/{email}"

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    response = requests.get(user_url, headers=headers)
    if response.status_code == 200:
        return response.json().get('id')
    else:
        raise Exception(f"Error fetching user ID: {response.json().get('error', {}).get('message', 'Unknown error')}")


def create_teams_meeting(email, subject, start_time, end_time):
    access_token = get_access_token()
    user_id = get_user_id(email)  # Fetch the user ID based on the email

    meeting_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/onlineMeetings"

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    data = {
        "subject": subject,
        "startDateTime": start_time,
        "endDateTime": end_time,
        "participants": {
            "organizer": {
                "identity": {
                    "user": {
                        "id": user_id  # Use the fetched user ID as organizer
                    }
                }
            }
        }
    }

    response = requests.post(meeting_url, headers=headers, json=data)

    print(f"Meeting creation response: {response.json()}")  # Log response to debug
    if response.status_code == 201:  # Check if meeting was created successfully
        return response.json()
    else:
        raise Exception(f"Error creating meeting: {response.json().get('error', {}).get('message', 'Unknown error')}")
