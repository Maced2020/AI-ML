# config.py

ROM_PATH = r"C:\path\to\Super Mario Bros. (World).nes"
EMULATOR_PATH = r"C:\path\to\fceux64.exe"

# Window title substring used to find the emulator window (case-sensitive substring search)
WINDOW_TITLE = "FCEUX"

SCREEN_REGION = {"top": 100, "left": 100, "width": 256, "height": 240}  # Adjust if the emulator is offset

# Simplified action space — long presses handled automatically in send_input()
ACTIONS = [
    'NONE', 'UP', 'DOWN', 'LEFT', 'RIGHT',
    'A', 'B', 'START',
    'RIGHT+A', 'RIGHT+B'
]

EPISODES = 3000
MAX_STEPS = 500