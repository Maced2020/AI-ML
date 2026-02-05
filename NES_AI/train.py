import sys
import time
import os
import numpy as np
import imageio
from config import EPISODES, MAX_STEPS, ACTIONS
from emulator_controller import launch_game, send_input
from screen_capture import get_frame
from replay_buffer import ReplayBuffer
from agent import Agent
from reward_tracker import RewardTracker
import memory_interface as mem


class RewardLogger:
    """Logs reward breakdown to CSV file for analysis."""
    
    def __init__(self, log_file='logs/reward_breakdown.csv'):
        """Initialize logger with CSV file path."""
        self.log_file = log_file
        self.flagpole_successes = 0
        self.episodes_logged = 0
        self.init_csv()
    
    def init_csv(self):
        """Create CSV file with header if it doesn't exist."""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        # Only write header if file doesn't exist
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                f.write('episode,total_reward,movement,points,progress,death,time,flagpole,stagnation,velocity_bonus,milestone,level_progression,time_out,max_x,epsilon,flagpole_success_rate\n')
    
    def log_episode(self, episode, total_reward, breakdown, max_x, epsilon, flagpole_reached):
        """Append episode data to CSV."""
        # Track flagpole success
        if flagpole_reached:
            self.flagpole_successes += 1
        self.episodes_logged += 1
        
        # Calculate success rate over last 10 episodes
        if self.episodes_logged >= 10:
            success_rate = self.flagpole_successes / min(10, self.episodes_logged)
        else:
            success_rate = 0.0
        
        # Reset counter every 10 episodes
        if self.episodes_logged >= 10:
            self.flagpole_successes = 0
            self.episodes_logged = 0
        
        with open(self.log_file, 'a') as f:
            f.write(f"{episode},{total_reward:.2f},{breakdown['movement']:.2f},{breakdown['points']:.2f},"
                   f"{breakdown['progress']:.2f},{breakdown['death']:.2f},"
                   f"{breakdown['time']:.2f},{breakdown['flagpole']:.2f},"
                   f"{breakdown['stagnation']:.2f},{breakdown['velocity_bonus']:.2f},{breakdown['milestone']:.2f},"
                   f"{breakdown['level_progression']:.2f},{breakdown['time_out']:.2f},"
                   f"{max_x},{epsilon:.3f},{success_rate:.2f}\n")

def reset_game():
    print("🔄 Waiting to return to title screen...")
    
    # Wait for dying/game_over/transition to settle (with timeout)
    settle_timeout = 30  # 15 seconds max
    settle_count = 0
    while mem.get_game_status() in ("game_over", "dying", "transition"):
        print(f"💀 Waiting to settle... ({mem.get_game_status()})")
        time.sleep(0.5)
        settle_count += 1
        if settle_count >= settle_timeout:
            print("⚠️ Settle timeout - forcing START press")
            send_input("START")
            time.sleep(1)
            break

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
        
        # Recovery: if stuck in unknown state, try pressing START
        elif status not in ("title", "playing", "game_over", "dying", "transition"):
            print(f"⚠️ Unknown state '{status}' - attempting START press")
            send_input("START")
            time.sleep(1)

        time.sleep(0.1)

    # Final fallback: press START multiple times to recover
    print("⚠️ Timeout waiting for title screen - attempting recovery")
    for attempt in range(3):
        print(f"🔧 Recovery attempt {attempt + 1}/3")
        send_input("START")
        time.sleep(1)
        if mem.get_game_status() == "playing":
            print("✅ Recovery successful!")
            return get_frame()
    
    print("❌ Recovery failed - returning current frame")
    return get_frame()

def create_video_writer(episode, fps=60):
    # Use imageio to write mp4s via ffmpeg
    os.makedirs("logs", exist_ok=True)
    return imageio.get_writer(f"logs/episode_{episode}.mp4", fps=fps)

def main():
    # Prevent running on Python versions that lack compatible prebuilt numpy/opencv wheels
    if sys.version_info.major == 3 and sys.version_info.minor >= 14:
        print("\n⚠️ Detected Python 3.14+. Prebuilt binary wheels for numpy/opencv may be unavailable on Windows.")
        print("Please install Python 3.11 or 3.12, create a virtual environment, and reinstall requirements.")
        print("See README.md for detailed steps.")
        return
    os.makedirs("logs", exist_ok=True)
    agent = Agent()
    memory = ReplayBuffer(10000)
    reward_tracker = RewardTracker()
    reward_logger = RewardLogger()
    agent.load_model()
    launch_game()
    print("\n" + "="*60)
    print("⏳ Please load the Lua script (bridge.lua) in FCEUX now.")
    print("   File → Lua → New Lua Script Window → Run bridge.lua")
    print("="*60)
    input("Press ENTER when the Lua script is loaded and running...")
    print("✅ Starting training in 3 seconds...")
    time.sleep(3)

    for episode in range(EPISODES):
        state = reset_game()
        reward_tracker.reset_episode()
        available_actions = [a for a in ACTIONS if a != "START"]
        video = create_video_writer(episode)

        total_reward = 0
        title_screen_count = 0

        for step in range(MAX_STEPS):
            status = mem.get_game_status()
            mx, my = mem.get_mario_position()
            print(f"🎮 Episode {episode}, Step {step}: Status = {status} | Pos = ({mx}, {my})")

            raw_frame = get_frame()
            frame = (raw_frame * 255).astype(np.uint8)
            # frame is grayscale 84x84; convert to RGB for writing
            frame_rgb = np.stack([frame] * 3, axis=-1)
            video.append_data(frame_rgb)

            if status != "playing":
                # If stuck on title screen during episode, press START twice (handles demo)
                if status == "title":
                    title_screen_count += 1
                    if title_screen_count >= 2:
                        print("🔧 Stuck on title screen - pressing START twice (demo prevention)")
                        send_input("START")
                        time.sleep(0.3)
                        send_input("START")
                        time.sleep(0.5)
                        title_screen_count = 0
                
                print("⏸️ Not in playing state.")
                time.sleep(0.1)
                continue
            
            # Reset counter when playing
            title_screen_count = 0

            action_idx = agent.select_action(state, available_actions)
            chosen_action = ACTIONS[action_idx]
            print(f"🎮 Action: {chosen_action}")
            send_input(chosen_action)

            next_state = raw_frame
            
            # Build game_state dict from memory_interface calls
            curr_x, curr_y = mem.get_mario_position()
            game_state = {
                'x': curr_x or 0,
                'score': mem.get_score(),
                'lives': mem.get_lives() or 3,
                'flagpole': mem.is_flagpole_triggered(),
                'world': mem.get_world(),
                'level': mem.get_level(),
                'time_remaining': mem.get_time_remaining()
            }
            
            # Calculate reward using RewardTracker
            reward, breakdown = reward_tracker.calculate_reward(game_state)
            
            # Log reward breakdown to console (only if non-zero)
            if reward != 0:
                log_parts = [f"Step {step} | R={reward:+.2f}"]
                
                # Always show these core components
                log_parts.append(f"Mv:{breakdown['movement']:.2f}")
                
                # Show other components only if non-zero
                if breakdown['points'] != 0:
                    log_parts.append(f"Pts:{breakdown['points']:.0f}")
                if breakdown['progress'] != 0:
                    log_parts.append(f"Pr:{breakdown['progress']:.0f}")
                if breakdown['death'] != 0:
                    log_parts.append(f"De:{breakdown['death']:.0f}")
                if breakdown['time'] != 0:
                    log_parts.append(f"Tm:{breakdown['time']:.2f}")
                if breakdown['flagpole'] != 0:
                    log_parts.append(f"Fl:{breakdown['flagpole']:.0f}")
                
                # Show new reward components if non-zero
                if breakdown['stagnation'] != 0:
                    log_parts.append(f"St:{breakdown['stagnation']:.2f}")
                if breakdown['velocity_bonus'] != 0:
                    log_parts.append(f"Vb:{breakdown['velocity_bonus']:.2f}")
                if breakdown['milestone'] != 0:
                    log_parts.append(f"Ms:{breakdown['milestone']:.0f}")
                if breakdown['level_progression'] != 0:
                    log_parts.append(f"Lv:{breakdown['level_progression']:.0f}")
                if breakdown['time_out'] != 0:
                    log_parts.append(f"TO:{breakdown['time_out']:.0f}")
                
                print(" | ".join(log_parts))

            done = mem.get_game_status() in ("game_over", "dying", "transition")

            memory.push(state, action_idx, reward, next_state, done)
            agent.train_step(memory)

            state = next_state
            total_reward += reward

            if done:
                print(f"⛔ Episode end — {mem.get_game_status()}")
                break

        video.close()
        agent.update_target()

        # Get episode summary and log to CSV
        summary = reward_tracker.get_episode_summary()
        flagpole_reached = reward_tracker.flagpole_triggered
        reward_logger.log_episode(episode, total_reward, summary, 
                                  reward_tracker.max_x, agent.epsilon, flagpole_reached)

        print(f"✅ Episode {episode} - Total Reward: {total_reward:.2f} - Epsilon: {agent.epsilon:.3f}")
        with open("logs/episode_log.txt", "a", encoding="utf-8") as f:
            f.write(f"Episode {episode} - Reward: {total_reward:.2f} - Epsilon: {agent.epsilon:.3f}\n")

        if episode % 10 == 0:
            agent.save_model()

if __name__ == "__main__":
    main()
