# Constants
RESULTS_DIR = "./Results"
SUCCESSFUL_UPLOAD = RESULTS_DIR + '/SuccessfulUpload'
FAILED_UPLOAD = RESULTS_DIR + '/FailedUpload'
API_NAME = "youtube"
API_VERSION = "v3"
SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]
VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")
INVALID_VIDEO_FILE_MSG = "Please specify a valid video file."
INVALID_TEXT_FILE_MSG = "Please specify a valid text file."
INVALID_NEW_DIR_MSG = "Please specify a valid new directory path."
VIDEO_TAGS = [
    "reddit", "reddit stories", "ask reddit", "reddit story",
    "best of reddit", "reddit top posts", "reddit thread", "reddit posts",
    "reddit funny", "best reddit posts", "reddit confessions", "r/ask reddit",
    "reddit threads", "reddit mysteries", "disturbing ask reddit threads",
    "reddit and chill", "reddit compilation", "tiktok", "tiktokvideo", "tiktokviral"
]