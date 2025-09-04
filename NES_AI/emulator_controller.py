# emulator_controller.py
# Launch & manage emulator + input

import subprocess
import time
import keyboard  # Low-level keyboard input
from config import EMULATOR_PATH, ROM_PATH

def launch_game():
    subprocess.Popen([EMULATOR_PATH, ROM_PATH])
    time.sleep(1.5)  # Let the emulator start

def send_input(action):
    key_map = {
        "UP": "w",
        "DOWN": "s",
        "LEFT": "a",
        "RIGHT": "d",
        "A": "x",
        "B": "z",
        "START": "enter",
    }

    keys = action.split('+')

    # === Apply long press only if action includes A or B ===
    if any(k in ["A", "B"] for k in keys):
        duration = 0.9  # Long press for jump/fire/run
    else:
        duration = 0.05  # Short tap for movement etc.

    for key in keys:
        if key in key_map:
            keyboard.press(key_map[key])

    time.sleep(duration)

    for key in keys:
        if key in key_map:
            keyboard.release(key_map[key])
