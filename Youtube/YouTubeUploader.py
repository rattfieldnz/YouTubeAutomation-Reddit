from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from tinydb import Query
import Google
import logging
from pathlib import Path
import os
import shutil
import sys
import datetime
import socket

project_dir = os.path.dirname( __file__ )
project_dir = os.path.join(project_dir, '..')
sys.path.append(project_dir)

import database
import constants
from utils.utils import generic_exception_message
from utils.utils import generic_http_exception_message
from utils.utils import create_directory

class YouTubeUploader:
    def __init__(self, args):
        self.args = args
        self.service = self.create_service()
        self.db = database.load_database()
        self.submission = Query()

    def create_service(self):
        load_dotenv()
        CLIENT_SECRETS_FILE = os.getenv("YT_CREDENTIAL_FILE")
        return Google.Create_Service(CLIENT_SECRETS_FILE, constants.API_NAME, constants.API_VERSION, constants.SCOPES)

    def upload(self):
        videofile = self.args.file

        if not os.path.exists(videofile):
            sys.exit(constants.INVALID_VIDEO_FILE_MSG)
            
        txtfile = os.path.splitext(videofile)[0] + '.txt'
        
        if not os.path.exists(txtfile):
            sys.exit(constants.INVALID_TEXT_FILE_MSG)

        try:
            upload_date_time = self.get_upload_date_time()
            request_body = {
                "snippet": {
                    "categoryId": self.args.category,
                    "title": self.args.title,
                    "description": self.args.description,
                    "tags": self.args.tags.split(",") if self.args.tags else [],
                },
                "status": {
                    "privacyStatus": self.args.privacy_status,
                    "selfDeclaredMadeForKids": str(self.args.made_for_kids),
                },
                "notifySubscribers": str(self.args.notify_subscribers),
            }
            response = self.upload_video(request_body, videofile)

            create_directory(constants.SUCCESSFUL_UPLOAD)
            create_directory(constants.PROCESSING_DIR)
            create_directory(constants.FAILED_UPLOAD)

            if response:
                video_id = response.get("id")
                
                print(f"Video uploaded successfully. Video ID: {video_id}")  
                
                self.move_files(videofile, txtfile, constants.SUCCESSFUL_UPLOAD)
                
                if self.args.reddit_thread_id:
                    if self.db.search(self.submission.id == str(self.args.reddit_thread_id)):
                        self.db.upsert({'youtubeid': response.get('id')}, self.submission.id == str(self.args.reddit_thread_id))
                    self.db.close()
            else:
                self.move_files(videofile, txtfile, constants.FAILED_UPLOAD)

        except HttpError as e:
            generic_http_exception_message(e)
            self.move_files(videofile, txtfile, constants.FAILED_UPLOAD)
        except Exception as e:
            generic_exception_message(e)
            self.move_files(videofile, txtfile, constants.FAILED_UPLOAD)

    def upload_video(self, request_body, media_file):

        if not os.path.exists(media_file):
            sys.exit(constants.INVALID_VIDEO_FILE_MSG)
            
        txtfile = os.path.splitext(media_file)[0] + '.txt'
        
        if not os.path.exists(txtfile):
            sys.exit(constants.INVALID_TEXT_FILE_MSG)
            
        try:
            socket.setdefaulttimeout(120000)
            response = self.service.videos().insert(
                part="snippet,status",
                body=request_body,
                media_body=MediaFileUpload(media_file)
            ).execute()

            return response
        except HttpError as e:
            logging.error(f"An HTTP Error has occurred while uploading the video: {e}")
            return None
        except Exception as e:
            generic_exception_message(e)
            return None

    def get_upload_date_time(self):
        now = datetime.datetime.now()
        return now.isoformat() + ".000Z"

    def move_files(self, videofile, txtfile, to_dir):
        if not os.path.exists(videofile):
            sys.exit(constants.INVALID_VIDEO_FILE_MSG)
        if not os.path.exists(txtfile):
            sys.exit(constants.INVALID_TEXT_FILE_MSG)
        if not os.path.exists(to_dir):
            sys.exit(constants.INVALID_NEW_DIR_MSG)
        try:
            move = shutil.move(videofile, to_dir)
            print(f"Video file moved to {move}.")
            move = shutil.move(txtfile, to_dir)
            print(f"Txt file moved to {move}.")
        except Exception as e:
            generic_exception_message(e)
