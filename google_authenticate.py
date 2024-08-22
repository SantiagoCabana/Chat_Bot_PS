from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import os
import pickle
import requests

# Credenciales de Google OAuth 2.0
GOOGLE_CREDENTIALS = {
    "installed": {
        "client_id": "577144044010-hk2mcps54jdoe59vgu95e9ookb8iau9u.apps.googleusercontent.com",
        "project_id": "save-contac-selenium",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "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",
        "redirect_uris": ["http://localhost"]
    }
}

# Ruta para almacenar el archivo token.pickle
TOKEN_PICKLE_PATH = os.path.join('DATA', 'tokens', 'pickle', 'token.pickle')

def google_authenticate():
    creds = None
    # El archivo token.pickle almacena las credenciales del usuario.
    if os.path.exists(TOKEN_PICKLE_PATH):
        with open(TOKEN_PICKLE_PATH, 'rb') as token:
            creds = pickle.load(token)
    # Si no hay credenciales válidas disponibles, el usuario debe iniciar sesión.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(GOOGLE_CREDENTIALS, [
                'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile',
                'https://www.googleapis.com/auth/contacts.readonly',
                'openid'
            ])
            creds = flow.run_local_server(port=0)
        # Guardar las credenciales para la próxima ejecución.
        os.makedirs(os.path.dirname(TOKEN_PICKLE_PATH), exist_ok=True)
        with open(TOKEN_PICKLE_PATH, 'wb') as token:
            pickle.dump(creds, token)
    return creds

def get_user_info(creds):
    user_info_endpoint = 'https://www.googleapis.com/oauth2/v1/userinfo'
    response = requests.get(user_info_endpoint, headers={'Authorization': f'Bearer {creds.token}'})
    return response.json()