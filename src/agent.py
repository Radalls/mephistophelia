import os
import pickle
import random

from src.constants import AGENT_ACTIONS, AGENT_LEARNING_MODES

class Agent:

    def __init__(self, x, y, x_bound, y_bound, learning_mode, learning_rate, discount_factor):
        self.start_x = x
        self.start_y = y
        self.state = None
        self.score = 0
        self.history = []
        self.noise = 0.0
        
        self.learning_mode = learning_mode
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.qtable = {}

        if self.is_learning_random():
            self.init_qtable(x_bound, y_bound)

    #region QTABLE
    def init_qtable(self, x_bound, y_bound):
        for state in self.get_all_states(x_bound, y_bound):
            self.qtable[state] = {}
            for action in self.get_all_actions():
                self.qtable[state][action] = 0.0

    def get_all_states(self, x_bound, y_bound):
        return [
            (x, y) for x in range(0, x_bound + 1)
            for y in range(0, y_bound + 1)
        ]

    def add_state(self, state):
        if state not in self.qtable:
            self.qtable[state] = {}
            for action in self.get_all_actions():
                self.qtable[state][action] = 0.0

    def get_all_actions(self):
        return AGENT_ACTIONS
    #endregion QTABLE

    #region ACTIONS
    def best_action(self):
        if self.noise > 0 and random.random() < self.noise:
            return self.random_action()
        return max(self.qtable[self.state], key=self.qtable[self.state].get)
    
    def random_action(self):
        return random.choice(AGENT_ACTIONS)
    
    def update(self, action, new_state, reward):
        if self.is_learning_radar():
            self.add_state(new_state)

        if self.noise > 0:
            self.noise -= 1E-4
        
        self.score += reward
        maxQ = max(self.qtable[new_state].values())
        delta = self.learning_rate * (reward + self.discount_factor * maxQ - self.qtable[self.state][action])
        self.qtable[self.state][action] += delta
        self.state = new_state
    
    def reset(self):
        self.history.append(self.score)
        self.score = 0
    #endregion ACTIONS
        
    #region SAVE
    def load_save(self, filename):
        if os.path.exists(filename):
            with open(filename, 'rb') as file:
                self.qtable = pickle.load(file)
    
    def save(self, filename):
        with open(filename, 'wb') as file:
            pickle.dump(self.qtable, file)
    #endregion DATA

    #region UTILS
    def is_learning_random(self):
        return self.learning_mode == AGENT_LEARNING_MODES[0]
    
    def is_learning_radar(self):
        return self.learning_mode == AGENT_LEARNING_MODES[1]
    #endregion UTILS
