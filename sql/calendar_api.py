from __future__ import print_function
import os.path
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_credentials():
    creds = None
    if os.path.exists('token2.json'):
        with open('token2.json', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token2.json', 'wb') as token:
            pickle.dump(creds, token)
    return creds

def create_calendar(service):
    calendar = {
        'summary': 'Citas',
        'timeZone': 'America/Los_Angeles'
    }
    created_calendar = service.calendars().insert(body=calendar).execute()
    print(f"Calendar created: {created_calendar['id']}")
    return created_calendar['id']

def create_event(service, calendar_id):
    event = {
        'summary': 'Consulta Médica',
        'location': 'Centro de Salud',
        'description': 'Consulta médica de rutina.',
        'start': {
            'dateTime': '2024-08-07T09:00:00-07:00',
            'timeZone': 'America/Los_Angeles',
        },
        'end': {
            'dateTime': '2024-08-07T10:00:00-07:00',
            'timeZone': 'America/Los_Angeles',
        },
        'attendees': [
            {'email': 'paciente@example.com'},
        ],
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }
    event_result = service.events().insert(calendarId=calendar_id, body=event).execute()
    print(f"Event created: {event_result['htmlLink']}")

def get_appointment_schedule_url(calendar_id):
    # URL de ejemplo para un calendario de citas
    schedule_url = f"https://calendar.google.com/calendar/u/0/appointments/schedules/{calendar_id}"
    return schedule_url

def delete_calendar(service, calendar_id):
    service.calendars().delete(calendarId=calendar_id).execute()
    print(f"Calendar {calendar_id} deleted")

def main():
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)

    calendar_id = create_calendar(service)
    create_event(service, calendar_id)

    # Obtener el enlace del calendario de citas
    appointment_schedule_url = get_appointment_schedule_url(calendar_id)
    print(f"Appointment Schedule URL: {appointment_schedule_url}")

    # Descomentar la siguiente línea para eliminar el calendario
    # delete_calendar(service, calendar_id)

if __name__ == '__main__':
    main()
