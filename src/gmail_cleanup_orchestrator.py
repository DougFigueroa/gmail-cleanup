from ctypes import create_unicode_buffer
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
import os.path
import base64
import email
from bs4 import BeautifulSoup


# define the scope of the API IF MODIFY IT, DELETE THE FILE token.json
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def get_credentials():
    """Get oauth credentials and store it in a local token file if its doesn't exists yet.
    """
    credentials = None
    if os.path.exists('token.json'):
        # read the token from the file
        credentials = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            credentials = flow.run_local_server(port=0)
        # save the credentials for the next execution
        with open('token.json', 'w') as token:
            token.write(credentials.to_json())
    return credentials


def get_emails(credentials):
    """Call the google api and get all the emails
    """
    results = None
    try:
        service = build('gmail', 'v1', credentials=credentials)
        results = service.users().messages().list(userId='me').execute()
    except HttpError as error:
        print(f'An error occured while getting emails: {error}')
    return results


def delete_emails():
    return


def handler():
    print('>> Starting the cleaning process...')
    # if not valid token, we will create a new one.
    credentials = get_credentials()
    email_batch = get_emails(credentials)
    print(email_batch)
    print('>> Cleaning complete. Enjoy :)')


if __name__ == '__main__':
    handler()
