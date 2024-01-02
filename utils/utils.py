from googleapiclient.errors import HttpError
import logging

DEFAULT_HTTP_TIMEOUT=300

def http_timeout() -> int:
    return DEFAULT_HTTP_TIMEOUT

def generic_exception_message(e: Exception):
    logging.exception(f"An exception has occurred: {e}")

def generic_http_exception_message(e: HttpError):
    logging.error(f"An HTTP Error has occurred: {e}")
