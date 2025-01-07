import gym
from gym import spaces
import numpy as np
import random
from stable_baselines3 import PPO  # PPO for policy optimization
from simulation.base_station import BaseStation
from simulation.user_equipment import UserEquipment

class MobileNetworkRLEnv(gym.Env):
    def __init__(self):
        super(MobileNetworkRLEnv, self).__init__()

        self.base_stations = []
        self.user_equipments = []
        self.current_ue_index = 0 

        self.action_space = spaces.Discrete(2)

        self.observation_space = spaces.Box(
            low=np.array([-np.inf, 0, 0, 0, 0]),
            high=np.array([np.inf, 6000, 6000, 6000, 6000]),
            dtype=np.float32
        )

        self.model = PPO("MlpPolicy", self, verbose=1)  
        self.reset()  
    def reset(self):
        self.base_stations = []  
        self.user_equipments = [] 
        self.init_simulation() 
        self.current_ue_index = 0 
        return self.get_state()

    def init_simulation(self):
        num_base_stations = 5  
        num_squares_per_bs = 350

        for i in range(num_base_stations):
            x = random.randint(100, 3000)
            y = random.randint(100, 3000)
            base_station = BaseStation(x, y)
            base_station.add_squares(num_squares_per_bs)
            self.base_stations.append(base_station)

        for bs in self.base_stations:
            for i in range(2):
                x = bs.x - random.randint(500, 2500)
                y = bs.y - random.randint(500, 1500)
                target_x = random.randint(bs.x - 50, bs.x + 50)
                target_y = random.randint(bs.y - 50, bs.y + 50)
                ue = UserEquipment(x=x, y=y, target_x=target_x, target_y=target_y)
                self.user_equipments.append(ue)

    def get_state(self):
        ue = self.user_equipments[self.current_ue_index]
        sinr = ue.serving_bs.signal_strength(ue) if ue.serving_bs else -np.inf
        state = np.array([sinr, ue.x, ue.y, ue.target_x, ue.target_y], dtype=np.float32)
        return state

    def step(self, action):
        ue = self.user_equipments[self.current_ue_index]
        

        if action == 1: 
            self.handle_handover(ue)


        for ue in self.user_equipments:
            ue.move()
            ue.update_signal_strength(self.base_stations)
        reward = self.calculate_reward(ue)

        
        next_state = self.get_state()
        done = self.check_done() 

        info = {}  

        return next_state, reward, done, info

    def handle_handover(self, ue):
        current_bs = ue.serving_bs
        best_bs = max(self.base_stations, key=lambda bs: bs.signal_strength(ue), default=None)
        if best_bs and best_bs != current_bs:
            ue.serving_bs = best_bs
            ue.handover_occurred = True

    def calculate_reward(self, ue):
        return ue.throughput 

    def check_done(self):
        return False 

    def train_agent(self, total_episodes=1000):
        for episode in range(total_episodes):
            state = self.reset()
            done = False
            
            while not done:
                action, _ = self.model.predict(state) 
                next_state, reward, done, _ = self.step(action)  
                self.model.replay_buffer.add(state, action, reward, next_state, done)
                

            self.model.learn(total_timesteps=1000, reset_num_timesteps=False)
