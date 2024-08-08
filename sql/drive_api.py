from __future__ import print_function
import os.path
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# Autenticación y autorización
SCOPES = ['https://www.googleapis.com/auth/drive']
CREDENTIALS_FILE = 'credentials.json'  # credenciales de api de google drive

def authenticate():
    creds = None
    # El archivo token.json almacena los tokens de acceso y actualización del usuario.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # Si no hay credenciales válidas disponibles, permite al usuario iniciar sesión.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Guarda las credenciales para la próxima ejecución.
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

service = build('drive', 'v3', credentials=authenticate())

# Subir archivo a Google Drive
def upload_file(file_name, file_path, mime_type, folder_id):
    # Crear archivo si no existe
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            f.write('')
            print(f'Archivo {file_path} creado')
    file_metadata = {'name': file_name, 'parents': [folder_id]}
    media = MediaFileUpload(file_path, mimetype=mime_type)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print('File ID: %s' % file.get('id'))

# Descargar archivo de Google Drive
def download_file(file_id, destination):
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(destination, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print("Download %d%%." % int(status.progress() * 100))

# Obtener el ID del archivo en Google Drive
def get_file_id(file_name, folder_id):
    query = f"'{folder_id}' in parents and name='{file_name}' and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name, size, modifiedTime)').execute()
    items = results.get('files', [])
    if not items:
        print('No files found.')
        return None
    else:
        return items

# Obtener el ID de la carpeta en Google Drive
def get_folder_id(folder_name):
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    print(f"Query: {query}")  # Agregar salida de depuración
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    items = results.get('files', [])
    if not items:
        print('No folders found.')
        return None
    else:
        print(f"Found folders: {items}")  # Agregar salida de depuración
        return items[0]['id']

# Eliminar archivo de Google Drive
def delete_file(file_id):
    service.files().delete(fileId=file_id).execute()
    print(f'File ID: {file_id} deleted.')

# Manejar duplicados
def handle_duplicates(files):
    if len(files) <= 1:
        return files

    # Ordenar por tamaño (descendente) y luego por fecha de modificación (ascendente)
    files.sort(key=lambda x: (int(x['size']), x['modifiedTime']), reverse=True)

    # Mantener el archivo con más peso o el de fecha de modificación más lejana
    main_file = files[0]
    duplicates = files[1:]

    for file in duplicates:
        delete_file(file['id'])

    return [main_file]

# Ejemplo de uso
if __name__ == '__main__':
    folder_name = 'Entrenamiento_chat_bot'
    archivos = ['entrenamiento.pkl']
    folder_id = get_folder_id(folder_name)
    if folder_id:
        print(f'Folder ID: {folder_id}')
        
        # Obtener todos los archivos en la carpeta
        query = f"'{folder_id}' in parents and trashed=false"
        results = service.files().list(q=query, spaces='drive', fields='files(id, name, size, modifiedTime)').execute()
        items = results.get('files', [])
        
        # Verificar y manejar archivos
        for archivo in archivos:
            files = [item for item in items if item['name'] == archivo]
            files = handle_duplicates(files)
            if not files:
                upload_file(archivo, archivo, 'application/octet-stream', folder_id)
                files = get_file_id(archivo, folder_id)
            if files:
                download_file(files[0]['id'], f'downloaded_{archivo}')
        
        # Eliminar archivos no deseados
        for item in items:
            if item['name'] not in archivos:
                delete_file(item['id'])