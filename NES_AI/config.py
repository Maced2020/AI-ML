# config.py

ROM_PATH = '''path to NES Rom'''
EMULATOR_PATH = '''path to fceux64.exe'''

SCREEN_REGION = {"top": 100, "left": 100, "width": 256, "height": 240}  # Adjust if the emulator is offset

# Simplified action space — long presses handled automatically in send_input()
ACTIONS = [
    'NONE', 'UP', 'DOWN', 'LEFT', 'RIGHT',
    'A', 'B', 'START',
    'RIGHT+A', 'RIGHT+B'
]

EPISODES = 5000
MAX_STEPS = 500