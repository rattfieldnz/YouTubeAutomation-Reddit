from Reddit import reddit
import config
from utils.utils import countdown

from VideoEditor.VideoProcessor import VideoProcessor

if __name__ == "__main__":
    my_config = config.load_config()
    my_reddit = reddit.login()
    
    video_processor = VideoProcessor(config=my_config)

    while True:
        print("Starting ..........\n")
        thread = reddit.get_thread(reddit=my_reddit, subreddit=my_config["Reddit"]["subreddit"])
        video_processor.process_thread(thread)
        print("\n-------------------------------------------\n")
        countdown(my_config)
