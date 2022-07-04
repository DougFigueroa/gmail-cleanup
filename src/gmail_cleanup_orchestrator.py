from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
from datetime import datetime
import os.path
import configparser


# define the scope of the API IF MODIFY IT, DELETE THE FILE token.json
SCOPES = ['https://mail.google.com/', 'https://www.googleapis.com/auth/gmail.readonly']  # this grants full access (read, delete, trash)
# SCOPES = ['https://www.googleapis.com/auth/gmail.readonly'] # use this if you want to only read messages


def read_config(file_path):
    parser = configparser.ConfigParser()
    parser.read(file_path)
    return parser


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


def get_emails(service, query=None, next_page=None):
    """Call the google api and get all the emails
    """
    results = None
    try:
        results = service.users().messages().list(userId='me', q=query, pageToken=next_page).execute()
        emails = results.get('messages')
        next_page_token = results.get('nextPageToken')
    except HttpError as error:
        print(f'An error occured while getting the email list: {error}')
    return emails, next_page_token


def get_email_content(service, email_id):
    """Get the email content: body and headers, and other metadata.
    """
    try:
        email_info = service.users().messages().get(userId='me', id=email_id).execute()
    except HttpError as error:
        print(f'An error occured while getting the email info: {error}')
    return email_info


def send_to_trash(service, email_id):
    """Sends emails to trash, we don't delete them directly to avoid any unwanted delete
    """
    result = None
    try:
        result = service.users().messages().trash(userId='me', id=email_id).execute()
    except HttpError as error:
        print(f'An error occured while sending the email to trash: {error}')
    return result


def handler():
    # this will be the words or queries to filter the search
    current_dir = os.path.dirname(__file__)
    config_file_path = os.path.join(current_dir, 'cfg', 'emails_to_filter.cfg')
    config = read_config(config_file_path)
    query_filters = config.get('email_filters', 'filter')
    # query = 'from:Amazon.com'
    start_time = datetime.now()
    print('>> Starting the cleaning process...')
    # if not valid token, we will create a new one.
    # create the service handler object to access the api
    service = build('gmail', 'v1', credentials=get_credentials())
    # start looping all of the filters
    for query in query_filters.split(','):
        next_page_token = None
        print(f'> Cleaning emails based on the filter-> {query}')
        while True:
            email_batch, next_page_token = get_emails(service, query=query, next_page=next_page_token)
            # send every email that meets the filter to trash
            if email_batch:
                for email in email_batch:
                    _result = send_to_trash(service, email.get('id'))
                    # print(f'Email sent it to trash: {result}')
            if not next_page_token:
                break
            # Use this section if you want list all the inbox and start reviewing email per email body and headers
            # for email in email_batch:
            #     email_info = get_email_content(service, email.get('id'))
            #     payload = email_info.get('payload')
            #     headers = payload.get('headers')
            #     body = base64.b64decode(payload.get('body').get('data').replace('-','+').replace('_','/'))
            #     # extract the headers that we need, in this case Subject and From
            #     for h in headers:
            #         if h.get('name') == 'Subject':
            #             subject = h.get('value')
            #         if h.get('name') == 'From':
            #             sender = h.get('value') 
            #     if 'quora' in subject.lower():
            #         # to do
            #       print(f'\n Email headers: {subject} |  {sender}')
            #       # get the lxml email body converted
            #       soup = BeautifulSoup(body, 'lxml')
            #       body_formatted = soup.body()
    end_time = datetime.now()
    duration = end_time - start_time
    print(f'>> Cleaning complete. Duration: {duration}. \n>> Hope you inbox is cleaner :)')


if __name__ == '__main__':
    handler()
