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
ASSIGNMENTS_URL = "https://mycourses.nic.bc.ca/d2l/le/worktodo/view"  # Replace with your actual URL

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
    username = "kcarmichael@northislandcollege.ca"
    password = "Puma6402!!"

    session = login_to_site(username, password)
    assignments = fetch_assignments(session)

    if assignments:
        print("Assignments fetched successfully. Adding to Google Calendar...")
        add_assignments_to_calendar(assignments)
    else:
        print("No assignments found or failed to fetch assignments.")

if __name__ == "__main__":
    main()

# selenium for dynamic content
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time

# Initialize a WebDriver session
def login_to_site(username, password):
    driver = webdriver.Chrome()  # Make sure you have the correct WebDriver installed
    driver.get(LOGIN_URL)

    # Locate and fill in the login form
    driver.find_element(By.ID, 'd2l_username').send_keys(username)  # Adjust the ID if necessary
    driver.find_element(By.ID, 'd2l_password').send_keys(password)
    driver.find_element(By.NAME, 'login').click()  # Adjust the name or type of the button

    # Wait for login to complete and assignments page to load
    time.sleep(5)  # You may need to adjust this depending on the site speed
    driver.get(ASSIGNMENTS_URL)

    return driver

# Fetch assignments using Selenium
def fetch_assignments(driver):
    assignments = []
    time.sleep(5)  # Ensure the page is fully loaded
    items = driver.find_elements(By.CLASS_NAME, 'assignment')  # Adjust class name as necessary

    for item in items:
        title = item.find_element(By.TAG_NAME, 'h2').text
        due_date = item.find_element(By.CLASS_NAME, 'due-date').text  # Adjust selectors
        assignments.append((title, due_date))

    return assignments
#check if google api is set up properly
def list_calendar_events():
    service = authenticate_google()
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(calendarId='primary', timeMin=now, maxResults=10, singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])
    
    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])
