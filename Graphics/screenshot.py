import json
import re
import config
import time
import socket
from pathlib import Path
from typing import Dict, Final

from playwright._impl._errors import TimeoutError
from playwright.async_api import async_playwright  # pylint: disable=unused-import
from playwright.sync_api import ViewportSize, sync_playwright

from dotenv import load_dotenv
import os
import constants
#from utils.imagenarator import imagemaker


def get_screenshots_of_reddit_posts(reddit_thread, reddit_comments, screenshot_num: int, theme="dark"):

    load_dotenv()
    
    my_config = config.load_config()
    
    Path("./logs/playwright").mkdir(parents=True, exist_ok=True)

    # settings values
    W = constants.DEFAULT_VID_WIDTH
    H = constants.DEFAULT_VID_HEIGHT

    reddit_id = re.sub(r"[^\w\s-]", "", reddit_thread.id)
    # ! Make sure the reddit screenshots folder exists
    Path(f"./Assets/temp/{reddit_id}/png").mkdir(parents=True, exist_ok=True)

    screenshot_num: int
    with sync_playwright() as p:
        print("Launching Headless Browser...")
        
        socket.setdefaulttimeout(constants.SOCKET_TIMEOUT)
        
        browser_config = my_config['App']['playwright_browser']
        
        p_browser = p.firefox
        
        if browser_config == 'chromium':
            p_browser = p.chromium
        elif browser_config == 'webkit':
            p_browser = p.webkit
            
        browser = p_browser.launch(headless=True)  # headless=False #to check for chrome view
        context = browser.new_context()
        # Device scale factor (or dsf for short) allows us to increase the resolution of the screenshots
        # When the dsf is 1, the width of the screenshot is 600 pixels
        # So we need a dsf such that the width of the screenshot is greater than the final resolution of the video
        dsf = (W // 600) + 1

        context = browser.new_context(
            locale="en-us",
            color_scheme="dark",
            viewport=ViewportSize(width=W, height=H),
            device_scale_factor=dsf,
        )
        
        context.set_default_timeout(constants.SOCKET_TIMEOUT)
        
        # set the theme and disable non-essential cookies
        if theme == "dark":
            cookie_file = open(
                "./Graphics/data/cookie-dark-mode.json", encoding="utf-8"
            )
            bgcolor = (33, 33, 36, 255)
            txtcolor = (240, 240, 240)


        cookies = json.load(cookie_file)
        cookie_file.close()

        context.add_cookies(cookies)  # load preference cookies

        # Get the thread screenshot
        page = context.new_page()
        page.set_default_timeout(constants.SOCKET_TIMEOUT)
        # go to reddit's login page
        page.goto("https://www.reddit.com/login/?experiment_d2x_2020ify_buttons=enabled&use_accountmanager=true&experiment_d2x_google_sso_gis_parity=enabled&experiment_d2x_onboarding=enabled&experiment_d2x_am_modal_design_update=enabled", timeout=constants.SOCKET_TIMEOUT)
        # fill user info
        page.screenshot(path='./logs/playwright/before_fill.png')
        page.locator("id=loginUsername").fill(os.getenv("REDDIT_USERNAME"))
        page.locator("id=loginPassword").fill(os.getenv("REDDIT_PASSKEY"))
        page.get_by_role("button", name="Log In").click()
        page.screenshot(path='./logs/playwright/after_fill.png')
        time.sleep(10)
        # go to the thread
        page.goto("https://www.reddit.com" + reddit_thread.permalink, timeout=constants.SOCKET_TIMEOUT)
        time.sleep(10)
        page.keyboard.press("Escape")
        
        page.goto("https://www.reddit.com" + reddit_thread.permalink, timeout=constants.SOCKET_TIMEOUT)
        page.set_viewport_size(ViewportSize(width=W, height=H))

        postcontentpath = f"./Assets/temp/{reddit_id}/png/title.png"
        page.locator(f'[data-test-id="post-content"]').screenshot(path=postcontentpath)
        print("Screenshot for OP completed")



        for idx, comment in enumerate(reddit_comments):


            if page.locator('[data-testid="content-gate"]').is_visible():
                page.locator('[data-testid="content-gate"] button').click()

            page.goto(f'https://reddit.com{comment.permalink}', timeout=constants.SOCKET_TIMEOUT)

            try:
                page.locator(f"#t1_{comment.id}").screenshot(
                    path=f"./Assets/temp/{reddit_id}/png/{idx}.png"
                )
                print(f"Screenshot for {idx + 1} comment out of {len(reddit_comments)}")
            except TimeoutError:
                print("TimeoutError: Skipping screenshot...")
                continue

        # close browser instance when we are done using it
        browser.close()

    print("Screenshots downloaded Successfully.")