import os
import pickle
import google.auth.transport.requests
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/contacts']
credentials_path = 'resource/credentials.json'
token_path = 'path/to/token.pickle'

def get_credentials():
    creds = None
    token_dir = os.path.dirname(token_path)
    
    if not os.path.exists(token_dir):
        os.makedirs(token_dir)
    
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(google.auth.transport.requests.Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return creds

def create_contact(first_name, last_name, email):
    creds = get_credentials()
    service = build('people', 'v1', credentials=creds)

    contact_body = {
        'names': [{'givenName': first_name, 'familyName': last_name}],
        'emailAddresses': [{'value': email}]
    }

    try:
        service.people().createContact(body=contact_body).execute()
        print(f'Contacto {first_name} {last_name} agregado exitosamente.')
    except HttpError as e:
        if e.resp.status == 403:
            print("Error 403: La API de People no está habilitada. Por favor, habilítala y vuelve a intentarlo.")
        else:
            print(f'Error al agregar el contacto: {e}')

# Ejemplo de uso
create_contact('Juan', 'Perez', 'juan.perez@example.com')