from dotenv import load_dotenv
from googleapiclient.errors import HttpError
from pathlib import Path
import argparse
import datetime
import logging
import os
import shutil
import sys
import socket

from YouTubeUploader import YouTubeUploader

project_dir = os.path.dirname( __file__ )
project_dir = os.path.join(project_dir, '..')
sys.path.append(project_dir )

import constants

def parse_args():

    privacy_statuses = constants.VALID_PRIVACY_STATUSES
    
    parser = argparse.ArgumentParser(description="Upload a video to YouTube")
    parser.add_argument("--file", required=True, help="Video file to upload")
    parser.add_argument("--reddit_thread_id", required=True, help="Reddit thread ID")
    parser.add_argument("--playlist_id", default="", help="Channel playlist ID.")
    parser.add_argument("--title", default="Test Title", help="Video title")
    parser.add_argument("--description", default="Test Description", help="Video description")
    parser.add_argument("--category", default="24", help="Numeric video category")
    parser.add_argument("--tags", default="", help="Video keywords, comma separated")
    parser.add_argument("--privacy_status", default=privacy_statuses[1], choices=privacy_statuses, help="Video privacy status")
    parser.add_argument("--made_for_kids", default=False, action="store_true", help="Is this video primarily made for kids")
    parser.add_argument("--notify_subscribers", default=False, action="store_true", help="Notify subscribers of new video upload")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    try:
        socket.setdefaulttimeout(120000)
        uploader = YouTubeUploader(args)
        uploader.upload()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)
    except Exception as e:
        logging.exception(e)
