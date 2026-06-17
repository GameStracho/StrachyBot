import io
import os
import datetime
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload  # type: ignore
from googleapiclient.discovery import build  # type: ignore
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from lib import console

def create_service(client_secret_file, api_name, api_version, *scopes, prefix=''):
    CLIENT_SECRET_FILE = client_secret_file
    API_SERVICE_NAME = api_name
    API_VERSION = api_version
    SCOPES = [scope for scope in scopes[0]]
    
    credentials = None
    working_dir = os.getcwd()
    token_dir = "./src/"
    token_file = f"token_{API_SERVICE_NAME}_{API_VERSION}{prefix}.json"

    ### Check if token dir exists first, if not, create the folder
    if not os.path.exists(os.path.join(working_dir, token_dir)):
        os.mkdir(os.path.join(working_dir, token_dir))

    if os.path.exists(os.path.join(working_dir, token_dir, token_file)):
        credentials = Credentials.from_authorized_user_file(os.path.join(working_dir, token_dir, token_file), SCOPES)
        # with open(os.path.join(working_dir, token_dir, token_file), 'rb') as token:
        #   cred = pickle.load(token)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            credentials = flow.run_local_server(port=0)

        with open(os.path.join(working_dir, token_dir, token_file), "w") as token:
            token.write(credentials.to_json())

    try:
        service = build(API_SERVICE_NAME, API_VERSION, credentials=credentials, static_discovery=False)
        console.log("GOOGLE", (
            API_SERVICE_NAME +
            f" {API_VERSION} " +
            "service created successfully."
        ))
        return service
    except Exception as e:
        print(e)
        console.log("GOOGLE", (
            f"Failed to create service instance for {API_SERVICE_NAME}"
        ))
        os.remove(os.path.join(working_dir, token_dir, token_file))
        return None


def convert_to_RFC_datetime(year=1900, month=1, day=1, hour=0, minute=0):
    dt = datetime.datetime(year, month, day, hour, minute, 0).isoformat() + "Z"
    return dt

CLIENT_SECRET_FILE = "./src/credentials.json"
API_NAME = "drive"
API_VERSION = "v3"
SCOPES = ["https://www.googleapis.com/auth/drive"]

service = create_service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

def upload_file(file_name: str):
    file_metadata = {
        "name": file_name,
        "parents": ["1vE4zPJWbXdBlqDoUPJ40hLSVkRNW0ILA"] # folder ids
    }

    media_content = MediaFileUpload(f"./src/{file_name}", mimetype="application/json")

    file = service.files().create(
        body=file_metadata,
        media_body=media_content
    ).execute()

    print(file)

    console.log("GOOGLE", f"File {file_name} successfully uploaded.")


def replace_file():
    file_id: str = "18A54d4_d5Nsil-E3uRJV1sYD_B3bVNwz"

    media_content = MediaFileUpload("./src/user_data.json", mimetype="application/json")

    service.files().update(
        fileId=file_id,
        media_body=media_content
    ).execute()

    console.log("GOOGLE", "File user_data.json successfully replaced.")


def download_file():
    file_id = "18A54d4_d5Nsil-E3uRJV1sYD_B3bVNwz"
    file_name = "user_data.json"
    
    request = service.files().get_media(fileId=file_id)
    
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fd=fh, request=request)

    done: bool = False

    while not done:
        status, done = downloader.next_chunk()
    
    console.log("GOOGLE", f"File {file_name} successfully downloaded.")
    
    fh.seek(0)
    
    with open(f"./src/{file_name}", "wb") as f:
        f.write(fh.read())
        f.close()
