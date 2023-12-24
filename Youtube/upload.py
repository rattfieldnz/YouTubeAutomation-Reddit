#!/usr/bin/python

import os
import sys
import datetime
import logging
import argparse
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
import Google
from dotenv import load_dotenv
import shutil
from pathlib import Path

from tinydb import Query
import os
import sys

project_dir = os.path.dirname( __file__ )
project_dir = os.path.join(project_dir, '..')
sys.path.append(project_dir )

import database

submission = Query()

# Constants
RESULTS_DIR = "./Results"
SUCCESSFUL_UPLOAD = RESULTS_DIR + '/SuccessfulUpload'
FAILED_UPLOAD = RESULTS_DIR + '/FailedUpload'
API_NAME = "youtube"
API_VERSION = "v3"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

def create_service():
    load_dotenv()
    
    CLIENT_SECRETS_FILE = os.getenv("YT_CREDENTIAL_FILE")
    
    return Google.Create_Service(CLIENT_SECRETS_FILE, API_NAME, API_VERSION, SCOPES)

def upload_video(service, request_body, media_file):
    try:
        response_upload = service.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media_file
        ).execute()

        # You can add code here to set video thumbnails if needed.
        # service.thumbnails().set(videoId=response_upload.get("id"), media_body=MediaFileUpload("thumbnail.png")).execute()

        return response_upload
    except HttpError as e:
        logging.error(f"HTTP Error: {e}")
        return None

def get_upload_date_time():
    now = datetime.datetime.now()
    return now.isoformat() + ".000Z"

def move_files(videofile: str, txtfile: str, to_dir: str):
    if not os.path.exists(videofile) or not os.path.exists(txtfile) or not os.path.exists(to_dir):
        sys.exit("Please specify a valid video file, text file, or new directory path.")
    try:
        move = shutil.move(videofile, to_dir)
        print(f"Video file moved to {move}.")
        move = shutil.move(txtfile, to_dir)
        print(f"Txt file moved to {move}.")
    except Exception as e:
        logging.exception(e)
        

def parse_args():
    parser = argparse.ArgumentParser(description="Upload a video to YouTube")
    parser.add_argument("--file", required=True, help="Video file to upload")
    parser.add_argument("--reddit_thread_id", required=True, help="Reddit thread ID")
    parser.add_argument("--title", default="Test Title", help="Video title")
    parser.add_argument("--description", default="Test Description", help="Video description")
    parser.add_argument("--category", default="24", help="Numeric video category")
    parser.add_argument("--tags", default="", help="Video keywords, comma separated")
    parser.add_argument("--privacy_status", default=VALID_PRIVACY_STATUSES[0], choices=VALID_PRIVACY_STATUSES, help="Video privacy status")
    parser.add_argument("--made_for_kids", default=False, action="store_true", help="Is this video primarily made for kids")
    parser.add_argument("--notify_subscribers", default=False, action="store_true", help="Notify subscribers of new video upload")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    db = database.load_database()
    
    if not os.path.exists(args.file):
        sys.exit("Please specify a valid file using the --file parameter.")

    videofile = args.file
    txtfile = RESULTS_DIR + '/Processing/' + args.reddit_thread_id + '.txt' 
    
    try:
        service = create_service()
        upload_date_time = get_upload_date_time()
        request_body = {
            "snippet": {
                "categoryId": args.category,
                "title": args.title,
                "description": args.description,
                "tags": args.tags.split(",") if args.tags else [],
            },
            "status": {
                "privacyStatus": args.privacy_status,
                #"publishAt": upload_date_time,
                "selfDeclaredMadeForKids": str(args.made_for_kids),
            },
            "notifySubscribers": str(args.notify_subscribers),
        }
        response = upload_video(service, request_body, args.file)

        Path(SUCCESSFUL_UPLOAD).mkdir(parents=True, exist_ok=True)
        Path(FAILED_UPLOAD).mkdir(parents=True, exist_ok=True)

        if response:
            print(f"Video uploaded successfully. Video ID: {response.get('id')}")
            if(args.reddit_thread_id is not None):
                if db.search(submission.id == str(args.reddit_thread_id)):
                    db.upsert({'youtubeid': response.get('id')}, submission.id == str(args.reddit_thread_id))
                db.close()
                
                move_files(videofile, txtfile, SUCCESSFUL_UPLOAD)
        else:
            move_files(videofile, txtfile, FAILED_UPLOAD)

    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)
    except Exception as e:
        logging.exception(e)
        move_files(videofile, txtfile, FAILED_UPLOAD)
