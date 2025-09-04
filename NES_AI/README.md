# NES_AI – Teaching an AI to Play Super Mario Bros.

This project is an experiment in building an **AI agent that plays Nintendo Entertainment System (NES) games**, starting with *Super Mario Bros.* (SMB1).  

The system connects to the **FCEUX 2.6.6 emulator** through a custom Lua script (`bridge.lua`). The Lua script exposes game state (Mario’s position, lives, status, etc.) and accepts button presses from Python. The Python side includes modules for capturing screen frames, shaping rewards, and training a neural network agent.

---

## How It Works
- **Screen Capture**: The AI sees the game frame-by-frame, downsampled and converted to grayscale.
- **Action Space**: The AI can press combinations of NES buttons (e.g. `RIGHT`, `B`, `A`) to move, run, and jump.
- **Rewards**: The AI is encouraged to move right, defeat enemies, collect power-ups, and finish levels. It is punished for dying, falling into pits, or stalling.
- **Training**: The agent uses a simplified Deep Q-Learning (DQN)-style loop with replay buffer and target network updates.

---

## Limitations
⚠️ This project is **not a perfect implementation of reinforcement learning**:
- The reward shaping does not work as intended (I don't think the AI is getting the rewards)
- currently you need to launch the Lua script after the train.py launches the emulator.
- State information is partly pulled from emulator memory, not purely raw pixels.
- Exploration/exploitation balance is still crude.
- Episodes may get stuck on menus or idle states.
- The AI can learn basic movement and short-term goals, but reliably *beating the game* is far beyond this setup without further tuning.

Think of this as a **prototype** or **learning project** in building game-playing AI, rather than a production-ready RL system.

---

## Usage
1. Install Python 3.10+ and dependencies (see `requirements.txt`).
2. Install FCEUX 2.6.6 on Windows.
3. Place a valid `mario.nes` ROM in your system and update the path in `config.py`.
4. Run training: 

python train.py


