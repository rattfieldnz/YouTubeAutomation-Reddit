from googleapiclient.errors import HttpError
import logging
import os
import sys
import time
from pathlib import Path

project_dir = os.path.dirname( __file__ )
project_dir = os.path.join(project_dir, '..')
sys.path.append(project_dir)

import constants
import config
import socket

from TextToSpeech.tts import create_tts
from TextToSpeech.TikTokVoice.tiktokvoice import tts, random_en_tiktok_voice

my_config = config.load_config()

def generic_exception_message(e: Exception):
    logging.exception(f"An exception has occurred: {e}")

def generic_http_exception_message(e: HttpError):
    logging.error(f"An HTTP Error has occurred: {e}")

def hashtags():
    hashtags = map(lambda x: str.replace(x, " ", ""), constants.VIDEO_TAGS)
    return [f'#{ht}' for ht in hashtags]

def create_directory(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)

def create_audio(text, path):

    socket.setdefaulttimeout(120000)
    tts(text=text, voice=random_en_tiktok_voice(), filename=path)

    if not os.path.exists(path):
        print(f"Audio file '{path}' doesn't exist. Trying Amazon Polly instead...")
        create_tts(text=text, path=path)

    if not os.path.exists(path):
        print(f"Audio file '{path}' doesn't exist, exiting...")
        exit()

def write_data_to_file(thread_id:str, thread_title:str, hashtags: str, tags: str):

    title_file = f"{constants.PROCESSING_DIR}/{thread_id}.txt"

    with open(title_file, "a") as f:
        f.write("Thread Title: " + thread_title)
        f.write("\n\nHashtags: " + hashtags)
        f.write("\n\nNormal Tags: " + tags + "\n\n")
        f.close()

def create_temp_asset_directories(thread_id):
    if(thread_id):
        thread_id_path = f"./Assets/temp/{thread_id}"
        create_directory(thread_id_path)
        create_directory(f"{thread_id_path}/mp3")
        create_directory(f"{thread_id_path}/mp3_clean")
        create_directory(f"{thread_id_path}/png")

def countdown(config):
    config_run_every = config["App"]["run_every"]
    if config_run_every:
        t = int(config_run_every)
        while t > 0 and t <= int(config_run_every):
            mins, secs = divmod(t, 60)
            hours, mins = divmod(mins, 60)
            timer = f'{hours:d} hours, {mins:02d} minutes, {secs:02d} seconds.'.format(hours, mins, secs)
            print("Time until next video processing: " + timer, end="\r", flush=True)
            time.sleep(1)
            t -= 1
