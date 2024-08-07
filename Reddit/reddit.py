import praw
from praw.reddit import Reddit
from praw.models import MoreComments
from tinydb import Query
from tinydb import where
import time
import config
import socket

from dotenv import load_dotenv
import os
import sys

project_dir = os.path.dirname( __file__ )
project_dir = os.path.join(project_dir, '..')
sys.path.append(project_dir )

import database
import constants
from utils.utils import generic_exception_message
from utils.utils import generic_http_exception_message

submission = Query()

def login():
    try:
        load_dotenv()
        my_config = config.load_config()
        reddit = praw.Reddit(
            client_id = os.getenv("REDDIT_CLIENT_ID"), 
            client_secret = os.getenv("REDDIT_CLIENT_SECRET"), 
            user_agent = os.getenv("REDDIT_USER_AGENT"),
            timeout = int(constants.SOCKET_TIMEOUT / 1000)
        )
        print("Logged in to Reddit successfully!")
        return reddit
    except Exception as e:
        generic_exception_message(e)
        return e

def get_thread(reddit: Reddit, subreddit: str):
    try:
        socket.setdefaulttimeout(constants.SOCKET_TIMEOUT)

        subreddit_ = reddit.subreddit(subreddit)
        threads = subreddit_.top('week')
    
        # Sort threads based on the number of up-votes
        sorted_threads = sorted(threads, key=lambda x: int(x.score), reverse=True)

        chosen_thread = None

        # Get the top-most up-voted thread that is not in the database
        db = database.load_database()
        for thread in sorted_threads:
            if not db.search(submission.id == str(thread.id)):
                db.upsert({'id': thread.id, 'time': time.time(), 'youtubeid': None}, submission.id == str(thread.id))
                print(f"Chosen thread: {thread.title} -- Score: {thread.score}")
                chosen_thread = thread
                break

        db.close()
        return chosen_thread
    except Exception as e:
        generic_exception_message(e)
        return None

def get_comments(thread):
    try:
        my_config = config.load_config()
        topn = my_config['Reddit']['topn_comments']
        chosen_comments = []
        comments = []

        for top_level_comment in thread.comments:
            if len(comments) == topn:
                break
            if isinstance(top_level_comment, MoreComments):
                continue
            comments.append(top_level_comment)

        chosen_comments = comments
        print(f"{len(chosen_comments)} comments are chosen.")
        return chosen_comments
    except Exception as e:
        generic_exception_message(e)
        return None

# Example usage:
# reddit = login()
# chosen_thread = get_thread(reddit, 'subreddit_name')
# chosen_comments = get_comments(chosen_thread)
