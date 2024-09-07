import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
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
        'username': username,
        'password': password,
        # Include any other hidden fields if necessary
    }

    session.post(LOGIN_URL, data=login_data)

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

# Step 2: Add assignments to Google Calendar
def create_event(service, title, due_date):
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

def add_assignments_to_calendar(assignments):
    creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/calendar'])
    service = build('calendar', 'v3', credentials=creds)

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
