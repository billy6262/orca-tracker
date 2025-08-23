from google_auth_oauthlib.flow import InstalledAppFlow



EmailPassword = 'aw4ergYUI%^Q@'
Email = 'orca73806@gmail.com'  #this emails only use is to recive reports
# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_token():
    creds = None
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    # Use a specific port and disable SSL verification for local testing
    creds = flow.run_local_server(
        port=8080,
        open_browser=True,
        success_message='The auth flow is complete, you may close this window.',
        authorization_prompt_message='Please visit this URL to authorize this application: '
    )
    
    # Save the credentials
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    print("Token has been saved to token.json")

if __name__ == '__main__':
    get_token()