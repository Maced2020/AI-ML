# memory_interface.py
import json
import os
import time

MEMORY_FILE = "mario_memory.json"

def _read_memory(retries=5, delay=0.01):
    for attempt in range(retries):
        if not os.path.exists(MEMORY_FILE):
            if attempt < retries - 1:
                time.sleep(delay)
                continue
            print("[MEM] ⚠️ Memory file not found.")
            return {}

        try:
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"[MEM] ❌ JSON decode error (attempt {attempt + 1}): {e}")
            time.sleep(delay)
        except Exception as e:
            print(f"[MEM] ❌ Unknown error reading memory file (attempt {attempt + 1}): {e}")
            time.sleep(delay)

    return {}

def get_mario_position():
    mem = _read_memory()
    return mem.get("mario_x", 0), mem.get("mario_y", 0)

def get_powerup_state():
    mem = _read_memory()
    return mem.get("powerup", "unknown")

def get_coin_count():
    mem = _read_memory()
    return mem.get("coins", 0)

def is_dead():
    mem = _read_memory()
    return mem.get("mario_dead", False)

def is_dying():
    return get_game_status() == "dying"

def get_game_status():
    mem = _read_memory()
    return mem.get("game_status", "unknown")

def is_playing():
    return get_game_status() == "playing"

def is_title_screen():
    return get_game_status() == "title"

def is_lives_screen():
    return get_game_status() == "lives_screen"

def is_game_over():
    return get_game_status() == "game_over"

def is_transitioning():
    return get_game_status() == "transition"

def is_flagpole_triggered():
    mem = _read_memory()
    return mem.get("flagpole", False)

def enemy_killed():
    mem = _read_memory()
    return mem.get("enemy_killed", False)

def q_block_hit():
    mem = _read_memory()
    return mem.get("q_block_hit", False)

def q_block_powerup():
    mem = _read_memory()
    return mem.get("q_block_powerup", False)

def is_stale(threshold_seconds=2):
    mem = _read_memory()
    ts = mem.get("timestamp", 0)
    if ts == 0:
        return True
    return (time.time() - ts) > threshold_seconds

def get_lives():
    mem = _read_memory()
    return mem.get("lives", None)

def life_lost():
    mem = _read_memory()
    return mem.get("life_lost", False)

def get_world():
    mem = _read_memory()
    return mem.get("world", 0)

def get_level():
    mem = _read_memory()
    return mem.get("level", 0)

def get_time_remaining():
    mem = _read_memory()
    return mem.get("time_remaining", 400)

def get_score():
    mem = _read_memory()
    return mem.get("_score", 0)
