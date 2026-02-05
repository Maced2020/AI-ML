# screen_capture.py
import pygetwindow as gw
import pyautogui
import numpy as np
from PIL import Image
from time import sleep
from config import WINDOW_TITLE


def get_frame():
    """Capture a grayscale downsampled 84x84 frame from the emulator window using Pillow.

    Waits for window to be focused before capturing.
    """
    while True:
        try:
            win = gw.getWindowsWithTitle(WINDOW_TITLE)[0]
            
            # Check if window is focused
            if not win.isActive:
                print(f"⚠️ Window not focused - please click on the emulator window to continue...")
                sleep(2)
                continue

            left, top, width, height = win.left, win.top, win.width, win.height
            screenshot = pyautogui.screenshot(region=(left, top, width, height))

            # screenshot is a PIL Image; convert, resize, and convert to grayscale
            img = screenshot.convert('RGB')
            img = img.resize((84, 84), Image.BILINEAR)
            img_gray = img.convert('L')
            arr = np.asarray(img_gray, dtype=np.uint8)
            return arr / 255.0

        except IndexError:
            print(f"[SCREEN] ❌ No window titled '{WINDOW_TITLE}' found - waiting...")
            sleep(2)
            continue
        except Exception as e:
            print(f"[SCREEN] ⚠️ Error capturing frame: {e} - retrying...")
            sleep(2)
            continue
