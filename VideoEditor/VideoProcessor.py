import os
import subprocess
import math
import textwrap

from utils.clean_text import markdown_to_text
from utils.add_mp3_pause import add_pause
from utils.utils import create_directory
from utils.utils import create_temp_asset_directories
from utils.utils import create_audio
from utils.utils import write_data_to_file
from utils.utils import hashtags
from utils.utils import generic_exception_message
from utils.utils import generic_http_exception_message
from TextToSpeech.tts import get_length
from VideoEditor.videomaker import make_final_video
from Graphics.screenshot import get_screenshots_of_reddit_posts
from Reddit import reddit
import config
import database
import constants
import socket

class VideoProcessor:
    def __init__(self, config):
        self.config = config

    def process_thread(self, thread):
        try:
            if thread is None:
                print("No thread found!")
                return

            socket.setdefaulttimeout(constants.SOCKET_TIMEOUT)

            comments = reddit.get_comments(thread=thread)
            if comments is None:
                print("No comments found!")
                return

            thread_id = thread.id
            thread_id_path = f"./Assets/temp/{thread_id}"\

            create_temp_asset_directories(thread_id)

            get_screenshots_of_reddit_posts(reddit_thread=thread, reddit_comments=comments, screenshot_num=1)

            print("Getting mp3 files..")

            thread_title = markdown_to_text(thread.title).replace("\"", "'")
            thread_title_truncated = textwrap.shorten(thread_title, 100, placeholder="")

            title_audio_path = f"{thread_id_path}/mp3/title.mp3"
            title_audio_clean_path = f"{thread_id_path}/mp3_clean/title.mp3"

            create_audio(thread_title, title_audio_path)

            comments_audio_path = []
            comments_audio_clean_path = []
            comments_image_path = []

            total_video_duration = self.config["VideoSetup"]["total_video_duration"]
            pause = int(self.config["VideoSetup"]["pause"])
            current_video_duration = 0
            mp3_pause = pause * 1000

            for idx, comment in enumerate(comments):
                path = f"{thread_id_path}/mp3/{idx}.mp3"
                comment_body = markdown_to_text(comment.body)

                create_audio(comment_body, path)

                comment_duration = get_length(path)
                print("Comment duration:", int(comment_duration or 0))

                if int(current_video_duration or 0) + int(comment_duration or 0) + pause <= total_video_duration:
                    comments_audio_path.append(path)
                    comments_audio_clean_path.append(f"{thread_id_path}/mp3_clean/{idx}.mp3")
                    comments_image_path.append(f"{thread_id_path}/png/{idx}.png")
                    current_video_duration += int(comment_duration or 0) + pause

            add_pause(title_audio_path, title_audio_clean_path, mp3_pause)
            for input_path, output_path in zip(comments_audio_path, comments_audio_clean_path):
                add_pause(input_path, output_path, mp3_pause)

            title_image_path = f"{thread_id_path}/png/title.png"
            create_directory(constants.PROCESSING_DIR)
            final_video_path = f"{constants.PROCESSING_DIR}/{thread_id}.mp4"

            make_final_video(
                title_audio_path=title_audio_clean_path,
                comments_audio_path=comments_audio_clean_path,
                title_image_path=title_image_path,
                comments_image_path=comments_image_path,
                length=math.ceil(total_video_duration),
                reddit_id=thread.id,
            )

            hashtags_as_string = ", ".join(hashtags())
            tags_as_string = ", ".join(constants.VIDEO_TAGS)

            write_data_to_file(thread_id, thread_title, hashtags_as_string, tags_as_string)

            if self.config["App"]["upload_to_youtube"]:
                self.upload_to_youtube(final_video_path, thread_id, thread_title_truncated, thread_title, hashtags_as_string,
                                       tags_as_string)

        except Exception as e:
            sys.exit(generic_exception_message(e))

    def upload_to_youtube(self, final_video_path, thread_id, thread_title_truncated, thread_title, hashtags_as_string,
                          tags_as_string):
        try:
            cmd = (
                f"/usr/bin/python3 {self.config['Directory']['path']}/Youtube/upload.py"
                f" --file {final_video_path}"
                f" --reddit_thread_id \"{thread_id}\""
                f" --title \"{thread_title_truncated}\""
                f" --description \"{thread_title}\n\n{hashtags_as_string}\""
                f" --tags \"{tags_as_string}\""
                f" --privacy_status private"
            )
            subprocess.call(cmd, shell=True)

        except HttpError as e:
            sys.exit(generic_http_exception_message(e))

        except Exception as e:
            sys.exit(generic_exception_message(e))
