# NES AI - Super Mario Bros. Deep Reinforcement Learning Agent

This project trains a **Deep Q-Network (DQN) agent** to play *Super Mario Bros.* on the Nintendo Entertainment System using reinforcement learning. The agent learns through trial and error, receiving rewards for forward progress, collecting coins, and avoiding obstacles.

## 🎮 Project Overview

The AI agent uses computer vision to capture the game screen, a Lua bridge to read game memory, and a neural network to learn optimal gameplay strategies through reinforcement learning. The agent progressively improves its performance over thousands of training episodes.

## 🏗️ Architecture

### Components

1. **DQN Neural Network** (`agent.py`)
   - 3-layer convolutional neural network
   - Processes 84x84 grayscale game frames
   - Outputs Q-values for 10 possible actions
   - Epsilon-greedy exploration strategy

2. **Reward System** (`reward_tracker.py`)
   - **Positive Rewards** (10x multiplier):
     - Forward movement: +0.5 per pixel
     - Score gains: points × 2.5
     - Milestones: +20 to +150 (every 50 pixels)
     - Flagpole touch: +10,000
   - **Penalties** (20x multiplier):
     - Stagnation: -10.0 per frame
     - Backward movement: -10.0 per frame
     - Death: -50.0
     - Time out: -2000.0

3. **Memory Interface** (`memory_interface.py`)
   - Lua bridge to FCEUX emulator
   - Reads Mario's position, score, lives, time
   - Detects flagpole completion

4. **Screen Capture** (`screen_capture.py`)
   - Captures game window in real-time
   - Converts to 84x84 grayscale for neural network

5. **Replay Buffer** (`replay_buffer.py`)
   - Stores experience tuples (state, action, reward, next_state, done)
   - Enables experience replay for stable learning

## 📋 Requirements

### Software
- Python 3.8+
- FCEUX 2.6.6 (NES emulator)
- Super Mario Bros. ROM (World version)

### Python Dependencies
```bash
pip install -r requirements.txt
```

Key packages:
- `torch` - PyTorch for neural networks
- `numpy` - Numerical operations
- `pillow` - Image processing
- `pygetwindow` - Window capture
- `mss` - Screen capture

## 🚀 Setup Instructions

### 1. Install FCEUX Emulator
Download FCEUX 2.6.6 from [fceux.com](http://fceux.com/web/download.html)

### 2. Configure Paths
Edit `config.py` with your paths:

```python
ROM_PATH = r"C:\path\to\Super Mario Bros. (World).nes"
EMULATOR_PATH = r"C:\path\to\fceux64.exe"
WINDOW_TITLE = "FCEUX"  # Emulator window title
```

### 3. Set Up Lua Bridge
1. Open FCEUX
2. Load the Super Mario Bros. ROM
3. Go to **File → Lua → New Lua Script Window**
4. Load `bridge.lua`
5. The script will create a memory interface for the agent

### 4. Adjust Screen Region (if needed)
If the emulator window is in a different position, adjust in `config.py`:

```python
SCREEN_REGION = {"top": 100, "left": 100, "width": 256, "height": 240}
```

## 🎯 Training the Agent

### Start Training
```bash
python train.py
```

The agent will:
1. Launch the emulator (if not already running)
2. Start training episodes
3. Save model checkpoints every 10 episodes to `models/dqn_model.pth`
4. Log progress to `logs/episode_log.txt` and `logs/test_reward_breakdown.csv`

### Training Configuration
Edit `config.py` to adjust:

```python
EPISODES = 3000        # Total training episodes
MAX_STEPS = 500        # Max steps per episode
```

### Action Space
The agent can perform 10 actions:
- `NONE` - No input
- `UP`, `DOWN`, `LEFT`, `RIGHT` - D-pad directions
- `A`, `B` - Jump and run buttons
- `START` - Pause
- `RIGHT+A`, `RIGHT+B` - Combined movements

## 📊 Monitoring Progress

### Real-time Logs
Watch training progress in the console:
```
Episode 464 - Reward: 6240.55 - Epsilon: 0.662
```

### Detailed Breakdown
Check `logs/test_reward_breakdown.csv` for per-episode metrics:
- Total reward
- Movement, points, progress rewards
- Death penalties, stagnation penalties
- Max X position reached
- Epsilon (exploration rate)

### Episode Log
Simple episode summary in `logs/episode_log.txt`

## 🧠 How It Works

### Training Loop
1. **Observe**: Capture game screen (84x84 grayscale)
2. **Decide**: Neural network selects action based on Q-values
3. **Act**: Send input to emulator via memory interface
4. **Learn**: Calculate reward, store experience, train network
5. **Repeat**: Continue until episode ends (death, time out, or flagpole)

### Epsilon-Greedy Exploration
- Starts at ε=1.0 (100% random actions)
- Decays to ε=0.05 (5% random) over 3000 episodes
- Decay rate: 0.999993 per training step
- Balances exploration vs. exploitation

### Experience Replay
- Stores last 10,000 experiences
- Samples random batches of 32 for training
- Breaks correlation between consecutive experiences
- Improves learning stability

## 📈 Expected Training Progress

The agent learns progressively over time:

### Early Training (Episodes 0-500)
- **Epsilon**: 1.0 → 0.65 (random → learned behavior)
- **Typical Distance**: X=200-800 pixels
- **Behavior**: Mostly random exploration, occasional forward progress

### Mid Training (Episodes 500-1500)
- **Epsilon**: 0.65 → 0.52
- **Typical Distance**: X=800-1500 pixels
- **Behavior**: Consistent forward movement, learns to avoid pits

### Advanced Training (Episodes 1500-3000)
- **Epsilon**: 0.52 → 0.45
- **Typical Distance**: X=1500-2500+ pixels
- **Behavior**: Optimized movement, potential flagpole completions

### Key Metrics to Track
- **Max X Position**: How far Mario travels (flagpole at X=3200)
- **Total Reward**: Combined score from all reward components
- **Velocity Bonus**: Indicates fast, aggressive forward play
- **Stagnation Penalty**: Shows if agent gets stuck

## 🔧 Troubleshooting

### Emulator Not Found
- Ensure FCEUX is running with the ROM loaded
- Check `WINDOW_TITLE` matches your emulator window
- Verify `EMULATOR_PATH` is correct

### Screen Capture Issues
- Adjust `SCREEN_REGION` to match your emulator position
- Ensure emulator window is visible (not minimized)
- Check screen scaling settings (100% recommended)

### Lua Bridge Not Working
- Reload `bridge.lua` in FCEUX Lua window
- Check FCEUX console for Lua errors
- Ensure ROM is loaded before running Lua script

### Training Too Slow
- Reduce `MAX_STEPS` for faster episodes
- Use GPU if available (PyTorch will auto-detect)
- Close other applications to free resources

## 🎓 Learning Resources

- [Deep Q-Learning Paper](https://www.nature.com/articles/nature14236) - Original DQN paper
- [OpenAI Spinning Up](https://spinningup.openai.com/) - RL fundamentals
- [FCEUX Documentation](http://fceux.com/web/help.html) - Emulator guide

## 📝 License

This project is for educational purposes. Super Mario Bros. is © Nintendo.

## 🙏 Acknowledgments

- FCEUX emulator team
- PyTorch community
- OpenAI for RL research

---

**Note**: Training a DQN agent requires patience! Early episodes will show mostly random behavior, but the agent progressively learns effective strategies over hundreds to thousands of episodes.
