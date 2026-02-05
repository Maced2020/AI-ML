"""
Reward tracking system for Super Mario Bros RL agent.
Centralizes reward calculation and state tracking across frames.
"""


class RewardTracker:
    """
    Tracks game state across frames and calculates rewards for the RL agent.
    
    Handles:
    - Coin collection rewards
    - Enemy kill rewards with cooldown
    - Forward progress rewards
    - Penalties (death, damage, time)
    - Flagpole completion rewards
    """
    
    def __init__(self):
        """Initialize reward tracker with state tracking variables."""
        # Previous state tracking
        self.prev_x = 0
        self.max_x = 0
        self.prev_lives = 3
        self.prev_score = 0
        
        # Flagpole tracking
        self.flagpole_triggered = False
        
        # Stagnation tracking
        self.x_history = []  # Last 30 X positions
        self.stagnation_threshold = 10  # Min pixels to move in 30 frames
        self.was_stuck = False  # Track if agent was stuck last check
        
        # Milestone tracking
        self.milestones_reached = set()
        
        # Level progression tracking
        self.prev_world = 0
        self.prev_level = 0
        
        # Time tracking
        self.prev_time = 400
        
        # Episode reward breakdown
        self.episode_rewards = {
            'movement': 0.0,
            'points': 0.0,
            'progress': 0.0,
            'death': 0.0,
            'time': 0.0,
            'flagpole': 0.0,
            'stagnation': 0.0,
            'velocity_bonus': 0.0,
            'milestone': 0.0,
            'level_progression': 0.0,
            'time_out': 0.0
        }
    
    def reset_episode(self):
        """Reset tracking for new episode."""
        self.prev_x = 0
        self.max_x = 0
        self.prev_lives = 3
        self.prev_score = 0
        self.flagpole_triggered = False
        
        # Reset stagnation tracking
        self.x_history = []
        self.was_stuck = False
        
        # Reset milestone tracking
        self.milestones_reached = set()
        
        # Reset level progression tracking
        self.prev_world = 0
        self.prev_level = 0
        
        # Reset time tracking
        self.prev_time = 400
        
        # Reset episode reward breakdown
        self.episode_rewards = {
            'movement': 0.0,
            'points': 0.0,
            'progress': 0.0,
            'death': 0.0,
            'time': 0.0,
            'flagpole': 0.0,
            'stagnation': 0.0,
            'velocity_bonus': 0.0,
            'milestone': 0.0,
            'level_progression': 0.0,
            'time_out': 0.0
        }
    
    def _calculate_points_reward(self, curr_score):
        """
        Calculate reward based on score increase.
        Rewards ANY point gain: coins, enemies, blocks, powerups, etc.
        Points × 2.5 = reward (100 points = +250.0, 500 points = +1250.0) - 10x INCREASE
        """
        score_gained = max(0, curr_score - self.prev_score)
        reward = score_gained * 2.5  # 10x INCREASE from 0.25
        self.prev_score = curr_score
        return reward
    
    def _calculate_movement_reward(self, curr_x):
        """Calculate enhanced movement rewards with velocity and milestones - 10x INCREASE."""
        # Continuous movement reward - 10x INCREASE
        delta_x = max(0, curr_x - self.prev_x)
        movement_reward = delta_x * 0.5  # 10x INCREASE from 0.05
        
        # Velocity bonus for fast movement - 10x INCREASE
        velocity_bonus = 0.0
        if delta_x > 20:
            velocity_bonus = 5.0  # 10x INCREASE from 0.5
        
        # "Unstuck" bonus - reward agent for moving after being stuck - 10x INCREASE
        if self.was_stuck and delta_x > 10:
            velocity_bonus += 20.0  # 10x INCREASE from 2.0
        
        # Update stuck status for next frame
        if len(self.x_history) >= 30:
            x_progress = curr_x - self.x_history[0]
            self.was_stuck = (x_progress < self.stagnation_threshold)
        
        # New max X bonus - 10x INCREASE
        progress_reward = 0.0
        if curr_x > self.max_x:
            progress_reward = 50.0  # 10x INCREASE from 5.0
            self.max_x = curr_x
        
        # Milestone bonuses (trigger once per episode) - 10x INCREASE
        # UPDATED: Continuous 50-pixel milestones for constant motivation
        milestone_reward = 0.0
        
        # Generate milestones every 50 pixels from 500 to 3200 (flagpole)
        # Reward increases as agent gets closer to flagpole
        for x in range(500, 3250, 50):
            if curr_x >= x and x not in self.milestones_reached:
                # Progressive rewards: more reward as you get closer to flagpole - 10x INCREASE
                if x < 1000:
                    bonus = 20.0      # 10x INCREASE from 2.0
                elif x < 1600:
                    bonus = 50.0      # 10x INCREASE from 5.0
                elif x < 2500:
                    bonus = 80.0      # 10x INCREASE from 8.0
                else:
                    bonus = 150.0     # 10x INCREASE from 15.0
                
                milestone_reward += bonus
                self.milestones_reached.add(x)
        
        self.prev_x = curr_x
        return movement_reward, progress_reward, velocity_bonus, milestone_reward
    
    def _calculate_penalties(self, curr_lives):
        """Calculate penalties for death and time."""
        death_penalty = 0.0
        time_penalty = -0.005
        
        # Death penalty
        if curr_lives < self.prev_lives:
            death_penalty = -50.0
            self.prev_lives = curr_lives
        
        return death_penalty, time_penalty
    
    def _calculate_stagnation_penalty(self, curr_x):
        """
        Penalize staying still or moving backward.
        
        Tracks X position over last 30 frames and applies BRUTAL penalties for:
        - Backward movement: -10.0 per frame (20x INCREASE from original -0.5)
        - Stagnation: -10.0 per frame when X hasn't increased by 10+ pixels in 30 frames (20x INCREASE from original -0.5)
        - Capped at -1000.0 per episode (20x INCREASE from original -50.0)
        
        Args:
            curr_x: Current X position
            
        Returns:
            float: Stagnation penalty (negative value or 0.0)
        """
        stagnation_penalty = 0.0
        
        # Add current X to history
        self.x_history.append(curr_x)
        
        # Keep only last 30 frames
        if len(self.x_history) > 30:
            self.x_history.pop(0)
        
        # Check for backward movement (immediate penalty) - BRUTAL 20x INCREASE
        if self.prev_x > 0 and curr_x < self.prev_x:
            stagnation_penalty -= 10.0  # 20x INCREASE from original -0.5
        
        # Check for stagnation (after 30 frames) - BRUTAL 20x INCREASE
        if len(self.x_history) >= 30:
            x_progress = curr_x - self.x_history[0]
            if x_progress < self.stagnation_threshold:
                stagnation_penalty -= 10.0  # 20x INCREASE from original -0.5
        
        # Cap stagnation penalty to prevent catastrophic failures
        # Check if adding this penalty would exceed the cap
        potential_total = self.episode_rewards['stagnation'] + stagnation_penalty
        if potential_total < -1000.0:  # 20x INCREASE from original -50.0
            # Only apply penalty up to the cap
            stagnation_penalty = -1000.0 - self.episode_rewards['stagnation']
        
        return stagnation_penalty
    
    def _calculate_flagpole_reward(self, flagpole_flag, curr_x):
        """
        Calculate massive flagpole rewards - 10x INCREASE.
        
        Provides:
        - Close to flagpole bonus: +50.0 per frame when X > 3000 (10x INCREASE)
        - Flagpole completion reward: +10000.0 (10x INCREASE)
        
        Args:
            flagpole_flag: Boolean indicating if flagpole was touched
            curr_x: Current X position
            
        Returns:
            float: Flagpole reward
        """
        flagpole_reward = 0.0
        
        # Close to flagpole bonus - 10x INCREASE
        if curr_x > 3000 and not self.flagpole_triggered:
            flagpole_reward += 50.0  # 10x INCREASE from 5.0
        
        # MASSIVE flagpole completion reward - 10x INCREASE
        if flagpole_flag and not self.flagpole_triggered:
            self.flagpole_triggered = True
            flagpole_reward += 10000.0  # 10x INCREASE from 1000.0
        
        return flagpole_reward
    
    def _calculate_level_progression_reward(self, curr_world, curr_level):
        """
        Calculate reward for progressing to a new level - 10x INCREASE.
        
        Provides:
        - New level bonus: +5000.0 when entering a new level/world (10x INCREASE)
        
        Args:
            curr_world: Current world number (0=World 1, 1=World 2, etc.)
            curr_level: Current level/area number (0=Level 1, 1=Level 2, etc.)
            
        Returns:
            float: Level progression reward
        """
        level_reward = 0.0
        
        # Check if we've progressed to a new level
        if (curr_world != self.prev_world or curr_level != self.prev_level):
            # Only award if we've actually started (not just initialization)
            if self.prev_world != 0 or self.prev_level != 0 or self.prev_x > 0:
                level_reward = 5000.0  # 10x INCREASE from 500.0
        
        # Update tracking
        self.prev_world = curr_world
        self.prev_level = curr_level
        
        return level_reward
    
    def _calculate_time_penalty(self, curr_time):
        """
        Calculate penalties for running out of time.
        
        Provides:
        - Time-out penalty: -2000.0 when time reaches 0 (20x INCREASE from original -100.0)
        
        Args:
            curr_time: Current time remaining (0-400)
            
        Returns:
            float: time_out_penalty
        """
        time_out_penalty = 0.0
        
        # BRUTAL time-out penalty - agent should NEVER let time run out
        if curr_time == 0 and self.prev_time > 0:
            time_out_penalty = -2000.0  # 20x INCREASE from original -100.0
        
        # Update tracking
        self.prev_time = curr_time
        
        return time_out_penalty
    
    def calculate_reward(self, game_state):
        """
        Calculate total reward and breakdown for current game state.
        
        Args:
            game_state: Dict containing current game state with keys:
                - x: Mario's X position
                - score: Current game score
                - lives: Current lives
                - flagpole: Boolean flag for flagpole touch
                - world: Current world number (0=World 1, 1=World 2, etc.)
                - level: Current level/area number (0=Level 1, 1=Level 2, etc.)
                - time_remaining: Time remaining (0-400)
        
        Returns:
            tuple: (total_reward, breakdown_dict)
        """
        # Extract game state
        curr_x = game_state.get('x', 0)
        curr_score = game_state.get('score', 0)
        curr_lives = game_state.get('lives', 3)
        flagpole = game_state.get('flagpole', False)
        curr_world = game_state.get('world', 0)
        curr_level = game_state.get('level', 0)
        curr_time = game_state.get('time_remaining', 400)
        
        # Calculate individual reward components
        points_reward = self._calculate_points_reward(curr_score)
        
        # Calculate stagnation penalty BEFORE movement reward updates prev_x
        stagnation_penalty = self._calculate_stagnation_penalty(curr_x)
        
        movement_reward, progress_reward, velocity_bonus, milestone_reward = self._calculate_movement_reward(curr_x)
        death_penalty, time_penalty = self._calculate_penalties(curr_lives)
        flagpole_reward = self._calculate_flagpole_reward(flagpole, curr_x)
        level_progression_reward = self._calculate_level_progression_reward(curr_world, curr_level)
        time_out_penalty = self._calculate_time_penalty(curr_time)
        
        # Build breakdown dictionary
        breakdown = {
            'movement': movement_reward,
            'points': points_reward,
            'progress': progress_reward,
            'death': death_penalty,
            'time': time_penalty,
            'flagpole': flagpole_reward,
            'stagnation': stagnation_penalty,
            'velocity_bonus': velocity_bonus,
            'milestone': milestone_reward,
            'level_progression': level_progression_reward,
            'time_out': time_out_penalty
        }
        
        # Accumulate episode rewards
        for key in breakdown:
            self.episode_rewards[key] += breakdown[key]
        
        # Calculate total reward
        total_reward = sum(breakdown.values())
        
        return total_reward, breakdown
    
    def get_episode_summary(self):
        """Get reward breakdown summary for the episode."""
        return self.episode_rewards.copy()
