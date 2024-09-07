import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os.path
import datetime

# URLs and API endpoints (adjust if necessary)
LOGIN_URL = "https://mycourses.nic.bc.ca/d2l/login"
ASSIGNMENTS_URL = "https://mycourses.nic.bc.ca/d2l/le/calendar/12345"  # Replace with your actual URL

# Step 1: Login to D2L platform and scrape assignments
def login_to_site(username, password):
    session = requests.Session()

    # Fetch login page and submit form
    login_page = session.get(LOGIN_URL)
    soup = BeautifulSoup(login_page.text, 'html.parser')

    # Fill in the login form (adjust fields according to the actual form fields on the website)
    login_data = {
        'd2l_username': username,  # Adjust field names according to the actual form fields
        'd2l_password': password,
        # Include any other hidden fields if necessary
    }

    # Find the form action URL and submit the form
    form_action = soup.find('form')['action']
    session.post(form_action, data=login_data)

    return session

def fetch_assignments(session):
    assignments_page = session.get(ASSIGNMENTS_URL)
    soup = BeautifulSoup(assignments_page.content, 'html.parser')

    # Parse assignment titles and due dates (adjust selectors according to actual page structure)
    assignments = []
    for item in soup.find_all('div', class_='assignment'):
        title = item.find('h2').text
        due_date = item.find('span', class_='due-date').text
        assignments.append((title, due_date))

    return assignments

# Step 2: Authenticate with Google and obtain Calendar service
def authenticate_google():
    creds = None
    # Token file stores the user's access and refresh tokens, and is created automatically
    # when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/calendar'])
    # If no valid credentials are available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', ['https://www.googleapis.com/auth/calendar'])
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('calendar', 'v3', credentials=creds)

# Step 3: Add assignments to Google Calendar
def create_event(service, title, due_date):
    try:
        # Convert string to datetime object
        due_date_dt = datetime.datetime.strptime(due_date, "%Y-%m-%d %H:%M:%S")

        event = {
            'summary': title,
            'start': {
                'dateTime': due_date_dt.isoformat(),
                'timeZone': 'America/Vancouver',
            },
            'end': {
                'dateTime': (due_date_dt + datetime.timedelta(hours=1)).isoformat(),
                'timeZone': 'America/Vancouver',
            },
        }

        event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Event created: {event.get('htmlLink')}")
    except Exception as e:
        print(f"Error creating event: {e}")

def add_assignments_to_calendar(assignments):
    service = authenticate_google()

    for title, due_date in assignments:
        create_event(service, title, due_date)

# Main function to run the script
def main():
    # Replace with your actual D2L login credentials
    username = "your_username"
    password = "your_password"

    session = login_to_site(username, password)
    assignments = fetch_assignments(session)

    if assignments:
        print("Assignments fetched successfully. Adding to Google Calendar...")
        add_assignments_to_calendar(assignments)
    else:
        print("No assignments found or failed to fetch assignments.")

if __name__ == "__main__":
    main()
