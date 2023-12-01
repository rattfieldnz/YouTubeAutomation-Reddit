import os
import subprocess
import time
import math
from pathlib import Path
from utils.clean_text import markdown_to_text
from utils.add_mp3_pause import add_pause
from VideoEditor.videomaker import make_final_video
from Graphics.screenshot import get_screenshots_of_reddit_posts
from TextToSpeech.tts import get_length, create_tts
from TextToSpeech.TikTokVoice.tiktokvoice import tts, random_en_tiktok_voice
import textwrap
from Reddit import reddit
import config
import sys
from tinydb import Query

import database

submission = Query()

# Constants
RESULTS_DIR = "./Results"

def main():
    my_config = config.load_config()
    my_reddit = reddit.login()
    db = database.load_database()
    
    thread = reddit.get_thread(reddit=my_reddit, subreddit=my_config["Reddit"]["subreddit"])

    if thread is None:
        print("No thread found!")
        return

    comments = reddit.get_comments(thread=thread)
    if comments is None:
        print("No comments found!")
        return

    # Create a temporary directory for the current thread
    thread_id = thread.id
        
    #if os.path.exists(RESULTS_DIR + "/" + thread.id + ".mp4"):
    #    print("Youtube video for thread ID " + thread.id + " has already been created!")
    #    return
    #else:
    
    thread_id_path = f"./Assets/temp/{thread_id}"
    Path(thread_id_path).mkdir(parents=True, exist_ok=True)

    # Download screenshot of Reddit post and its comments
    get_screenshots_of_reddit_posts(reddit_thread=thread, reddit_comments=comments, screenshot_num=1)

    # Create directories for mp3 and cleaned mp3 files
    Path(f"{thread_id_path}/mp3").mkdir(parents=True, exist_ok=True)
    Path(f"{thread_id_path}/mp3_clean").mkdir(parents=True, exist_ok=True)
    print("Getting mp3 files..")

    # Download TTS files for the title and comments
    thread_title = markdown_to_text(thread.title).replace("\"", "'")
    
    # Youtube limits video title lengths to 100 characters
    tiktok_title_append = " (Tiktok voices)"
    thread_title_truncated = textwrap.shorten(thread_title, 100 - len(tiktok_title_append), placeholder="")
    thread_title_truncated += tiktok_title_append 
    
    title_audio_path = f"{thread_id_path}/mp3/title.mp3"
    title_audio_clean_path = f"{thread_id_path}/mp3_clean/title.mp3"
    
    #Tiktok API voice:
    tts(text=thread_title, voice=random_en_tiktok_voice(), filename=title_audio_path)

    comments_audio_path = []
    comments_audio_clean_path = []
    comments_image_path = []

    # Calculate total video duration and add pauses
    total_video_duration = my_config["VideoSetup"]["total_video_duration"]
    pause = int(my_config["VideoSetup"]["pause"])
    current_video_duration = 0
    mp3_pause = pause * 1000

    for idx, comment in enumerate(comments):
        path = f"{thread_id_path}/mp3/{idx}.mp3"
        comment_body = markdown_to_text(comment.body)
        
        #Tiktok API voice:
        tts(text=comment_body, voice=random_en_tiktok_voice(), filename=path)
        
        #If Tiktok voice file not created, try Amazon Polly instead
        if not os.path.exists(path):
            print("Audio file '" + path + "'doesn't exist. Trying Amazon Polly instead...")
            create_tts(text=comment_body, path=path)
            
        # If Amazon Polly voice file not created, print warning then exit.
        if not os.path.exists(path):
            print("Audio file '" + path + "' doesn't exist, exiting...")
            exit()
            
        comment_duration = get_length(path)
        print("Comment duration: " + str(int(comment_duration or 0)))

        if int(current_video_duration or 0) + int(comment_duration or 0) + pause <= total_video_duration:
            comments_audio_path.append(path)
            comments_audio_clean_path.append(f"{thread_id_path}/mp3_clean/{idx}.mp3")
            comments_image_path.append(f"{thread_id_path}/png/{idx}.png")
            current_video_duration += int(comment_duration or 0) + pause

    # Add pauses to audio files
    add_pause(title_audio_path, title_audio_clean_path, mp3_pause)
    for input_path, output_path in zip(comments_audio_path, comments_audio_clean_path):
        add_pause(input_path, output_path, mp3_pause)

    # Create directories and paths
    title_image_path = f"{thread_id_path}/png/title.png"
    Path(RESULTS_DIR).mkdir(parents=True, exist_ok=True)
    final_video_path = f"{RESULTS_DIR}/{thread_id}.mp4"

    # Create the final video
    make_final_video(
        title_audio_path=title_audio_clean_path,
        comments_audio_path=comments_audio_clean_path,
        title_image_path=title_image_path,
        comments_image_path=comments_image_path,
        length=math.ceil(total_video_duration),
        reddit_id=thread.id,
        #output_path=final_video_path
    )

    title_file = f"{RESULTS_DIR}/{thread_id}.txt"
    
    tags = [
        "reddit", "reddit stories", "ask reddit", "reddit story",
        "best of reddit", "reddit top posts", "reddit thread", "reddit posts",
        "reddit funny", "best reddit posts", "reddit confessions", "r/ask reddit",
        "reddit threads", "reddit mysteries", "disturbing ask reddit threads",
        "reddit and chill", "reddit compilation", "tiktok", "tiktokvideo", "tiktokviral"
    ]
    
    hashtags = map(lambda x: str.replace(x, " ", ""), tags)
    hashtags = [f'#{ht}' for ht in hashtags]
    hashtags_as_string = ", ".join(hashtags)
    tags_as_string = ", ".join(tags)
    
    with open(title_file, "a") as f:
        f.write("Thread Title: " + thread_title + " (Tiktok voices)")
        f.write("\n\nHashtags: " + hashtags_as_string)
        f.write("\n\nNormal Tags: " + tags_as_string + "\n\n")
        f.close()
        
    if my_config["App"]["upload_to_youtube"]:

        cmd = (
            f"/usr/bin/python3 {my_config['Directory']['path']}/Youtube/upload.py" 
            f" --file {final_video_path}"
            f" --title \"{thread_title_truncated}\"" 
            f" --description \"{thread_title}\n\n{hashtags_as_string}\"" 
            f" --tags \"{tags_as_string}\"" 
            f" --reddit_thread_id \"{thread_id}\"" 
            f" --privacy_status private"
        )
        subprocess.call(cmd, shell=True)

def countdown(t): 
    
    while t > 0 and t <= int(my_config["App"]["run_every"]): 
        mins, secs = divmod(t, 60) 
        hours, mins = divmod(mins, 60)
        timer = f'{hours:d} hours, {mins:02d} minutes, {secs:02d} seconds.'.format(hours, mins, secs) 
        print("Time until next video processing: " + timer, end="\r", flush=True) 
        time.sleep(1) 
        t -= 1

if __name__ == "__main__":
    my_config = config.load_config()
    while True:
        print("Starting ..........\n")
        main()
        print("\n-------------------------------------------\n")
        countdown(my_config['App']['run_every'])