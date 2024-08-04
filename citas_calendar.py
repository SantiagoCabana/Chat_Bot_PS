import os
import pickle
import random
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Configurar los alcances necesarios para la API
SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/spreadsheets']

def authenticate_google_services():
    creds = None
    # El archivo token.pickle almacena las credenciales del usuario
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # Si no hay credenciales válidas, permite al usuario iniciar sesión
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Guarda las credenciales para la próxima ejecución
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

creds = authenticate_google_services()
calendar_service = build('calendar', 'v3', credentials=creds)
sheets_service = build('sheets', 'v4', credentials=creds)

class CalendarManager:
    def __init__(self, max_calendars):
        self.max_calendars = max_calendars
        self.calendars = self.initialize_calendars()
        self.calendar_to_sheet_map = {}

    def initialize_calendars(self):
        # Supongamos que ya tenemos algunos calendarios creados y sus IDs
        existing_calendars = ['calendar_id_1', 'calendar_id_2', 'calendar_id_3']
        if len(existing_calendars) > self.max_calendars:
            return existing_calendars[:self.max_calendars]
        return existing_calendars

    def get_available_calendar(self):
        return random.choice(self.calendars)

    def create_event(self, summary, location, description, start_time, end_time, calendar_id):
        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'America/Los_Angeles',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'America/Los_Angeles',
            },
        }

        event = calendar_service.events().insert(calendarId=calendar_id, body=event).execute()
        print(f'Event created: {event.get("htmlLink")}')
        return event

    def save_event_to_sheet(self, event, spreadsheet_id, range_name):
        values = [
            [event['summary'], event['location'], event['description'], event['start']['dateTime'], event['end']['dateTime']]
        ]
        body = {
            'values': values
        }
        result = sheets_service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption='RAW', body=body).execute()
        print(f'{result.get("updates").get("updatedCells")} cells appended.')

    def assign_calendar_to_sheet(self, calendar_id, spreadsheet_id):
        self.calendar_to_sheet_map[calendar_id] = spreadsheet_id

    def schedule_event(self, summary, location, description, start_time, end_time):
        calendar_id = self.get_available_calendar()
        event = self.create_event(summary, location, description, start_time, end_time, calendar_id)
        spreadsheet_id = self.calendar_to_sheet_map.get(calendar_id, 'default_spreadsheet_id')
        self.save_event_to_sheet(event, spreadsheet_id, 'Sheet1!A:D')
        
        # Retornar el link del evento y el nombre del archivo de Google Sheets
        spreadsheet_name = self.get_sheet_name(spreadsheet_id)
        return event.get("htmlLink"), spreadsheet_name
    
    def get_sheet_name(self, spreadsheet_id):
        spreadsheet = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        return spreadsheet.get('properties', {}).get('title', 'Unknown Spreadsheet')

# Ejemplo de uso
max_calendars = 5
calendar_manager = CalendarManager(max_calendars)

# Asignar calendarios a hojas de Google Sheets específicas
calendar_manager.assign_calendar_to_sheet('calendar_id_1', 'spreadsheet_id_1')
calendar_manager.assign_calendar_to_sheet('calendar_id_2', 'spreadsheet_id_2')
calendar_manager.assign_calendar_to_sheet('calendar_id_3', 'spreadsheet_id_3')

# Crear y registrar eventos
event_link, sheet_name = calendar_manager.schedule_event(
    summary='Reunión de Proyecto',
    location='Oficina',
    description='Discusión sobre el progreso del proyecto.',
    start_time='2024-08-10T10:00:00-07:00',
    end_time='2024-08-10T11:00:00-07:00'
)

print(f'Event link: {event_link}')
print(f'Spreadsheet name: {sheet_name}')
