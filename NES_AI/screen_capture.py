# screen_capture.py
import pygetwindow as gw
import pyautogui
import numpy as np
import cv2
from time import sleep

WINDOW_TITLE = "FCEUX 2.6.6: Super_Mario_Bros"

def get_frame():
    """
    Capture a grayscale downsampled 84x84 frame from the emulator window.
    """
    try:
        win = gw.getWindowsWithTitle(WINDOW_TITLE)[0]
        if not win.isActive:
            win.activate()
            sleep(0.1)

        left, top, width, height = win.left, win.top, win.width, win.height
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        img = np.array(screenshot)[..., :3]  # Drop alpha channel
        img = cv2.resize(img, (84, 84))
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return img_gray / 255.0

    except IndexError:
        print(f"[SCREEN] ❌ No window titled '{WINDOW_TITLE}' found.")
        return np.zeros((84, 84))  # fallback
