from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import mimetypes
import sqlite3
from typing import Dict 


def get_token(credentials_path: str='credentials.json', token_path: str='google_token.pickle') -> Request:
    """Get token/credentials"""
    # If modifying these scopes, delete the file token.pickle.
    # Just give master admin for the sake of simplicity
    SCOPES = ['https://www.googleapis.com/auth/drive']
    creds = None
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            creds = flow.run_local_server()  # This needs localhost
        # Save the credentials for the next run
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    drive_service = build('drive', 'v3', credentials=creds)

    return drive_service


def upload_media(drive_service: Request, folder_id: str, file_name: str) -> None:
    """Upload media - based on mimetype (in this case we only care about jpeg/mp4)"""
    file_metadata = {
        'name': file_name,
        'parents': [folder_id],
    }
    mimetype = mimetypes.guess_type(file_name)
    if mimetype is None:
        raise Exception(
            'unknown filetype, unable to find mimetype, easiest way is to zip them')
    media = MediaFileUpload(file_name,
                            chunksize=1048576,  # MUST be multiple of 256
                            mimetype=mimetype,
                            resumable=True)
    drive_file = drive_service.files().create(body=file_metadata,
                                              media_body=media,
                                              fields='id').execute()
    print('File - {0} Uploaded, File ID - {1}'.format(file_name,
                                                      drive_file.get('id')))


def make_directory(drive_service: Request, folder_id: str, new_folder_name: str) -> None:
    """This should make an empty directory in the folder_id with name, new_folder_name"""
    file_metadata = {
        'name': new_folder_name,
        'parents': [folder_id],
        'mimeType': 'application/vnd.google-apps.folder',
    }

    new_folder = drive_service.files().create(body=file_metadata,
                                              fields='id').execute()
    print('Folder - {0} Uploaded, File ID - {1}'.format(new_folder_name,
                                                        new_folder.get('id')))


def list_dir(drive_service: Request, folder_id: str) -> Dict[str, str]:
    """This will list all files of the directory"""
    items = drive_service.files().list(pageSize=1000,
                                       q=f'"{folder_id}" in parents').execute().get('files', [])
    res = {}
    for item in items:
        res[item['name']] = item['id']
    return res

if __name__ == "__main__":
    print('__main__')
