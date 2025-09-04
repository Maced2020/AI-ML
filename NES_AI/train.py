import time
import os
import numpy as np
import cv2
from config import EPISODES, MAX_STEPS, ACTIONS
from emulator_controller import launch_game, send_input
from screen_capture import get_frame
from replay_buffer import ReplayBuffer
from agent import Agent
import memory_interface as mem

def reset_game():
    print("🔄 Waiting to return to title screen...")
    while mem.get_game_status() in ("game_over", "dying", "transition"):
        print(f"💀 Waiting to settle... ({mem.get_game_status()})")
        time.sleep(0.5)

    for i in range(120):
        status = mem.get_game_status()
        print(f"🔍 Checking game status... ({i}): {status}")

        if status == "title":
            print("🟦 Title screen detected — pressing START.")
            time.sleep(0.5)
            send_input("START")
            time.sleep(0.5)

            for j in range(100):
                current_status = mem.get_game_status()
                x, y = mem.get_mario_position()
                print(f"⏳ Waiting for gameplay... ({j}) status:{current_status} pos:({x},{y})")
                if current_status == "playing" or (x and y and x > 0 and y > 0):
                    print("▶️ Game has started.")
                    return get_frame()
                time.sleep(0.1)

            print("⚠️ START pressed, but not playing.")
            break

        elif status == "playing":
            print("✅ Already playing.")
            return get_frame()

        time.sleep(0.1)

    print("⚠️ Timeout waiting for title screen.")
    return get_frame()

def create_video_writer(episode, fps=60):
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    return cv2.VideoWriter(f"logs/episode_{episode}.mp4", fourcc, fps, (84, 84))

def main():
    os.makedirs("logs", exist_ok=True)
    agent = Agent()
    memory = ReplayBuffer(10000)
    agent.load_model()
    launch_game()
    time.sleep(5)

    for episode in range(EPISODES):
        state = reset_game()
        prev_x, _ = mem.get_mario_position()
        prev_lives = mem.get_lives()
        available_actions = [a for a in ACTIONS if a != "START"]
        video = create_video_writer(episode)

        total_reward = 0

        for step in range(MAX_STEPS):
            status = mem.get_game_status()
            mx, my = mem.get_mario_position()
            print(f"🎮 Episode {episode}, Step {step}: Status = {status} | Pos = ({mx}, {my})")

            raw_frame = get_frame()
            frame = (raw_frame * 255).astype(np.uint8)
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            video.write(frame)

            if status != "playing":
                print("⏸️ Not in playing state.")
                time.sleep(0.1)
                continue

            action_idx = agent.select_action(state, available_actions)
            chosen_action = available_actions[action_idx]
            print(f"🎮 Action: {chosen_action}")
            send_input(chosen_action)

            next_state = raw_frame
            curr_x, _ = mem.get_mario_position()

            # ✅ Reward for moving right
            delta_x = max((curr_x or 0) - (prev_x or 0), 0)
            prev_x = curr_x
            reward = float(delta_x) * 0.1

            # ✅ Reward for enemy kill
            if mem.enemy_killed():
                reward += 1.0
                print("💥 Enemy killed! +1")

            # ✅ Reward for flagpole
            if mem.is_flagpole_triggered():
                reward += 5.0
                print("🏁 Flagpole triggered! +5")

            # ✅ Penalty for dying via lives check
            curr_lives = mem.get_lives()
            if curr_lives < prev_lives:
                reward -= 2.0
                print("☠️ Life lost! -2")
            prev_lives = curr_lives

            # Optional backup (not modifying reward)
            if mem.is_dead():
                print("☠️ Detected dead state (fallback).")

            done = mem.get_game_status() in ("game_over", "dying", "transition")

            memory.push(state, action_idx, reward, next_state, done)
            agent.train_step(memory)

            state = next_state
            total_reward += reward

            if done:
                print(f"⛔ Episode end — {mem.get_game_status()}")
                break

        video.release()
        agent.update_target()

        print(f"✅ Episode {episode} - Total Reward: {total_reward:.2f} - Epsilon: {agent.epsilon:.3f}")
        with open("logs/episode_log.txt", "a", encoding="utf-8") as f:
            f.write(f"Episode {episode} - Reward: {total_reward:.2f} - Epsilon: {agent.epsilon:.3f}\n")

        if episode % 10 == 0:
            agent.save_model()

if __name__ == "__main__":
    main()
