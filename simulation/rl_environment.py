import gym
from gym import spaces
import numpy as np
import random
from simulation.environment import Environment
from simulation.base_station import BaseStation
from simulation.user_equipment import UserEquipment

class MobileNetworkRLEnv(gym.Env):
    def __init__(self):
        super(MobileNetworkRLEnv, self).__init__()

        self.grid_size = 200
        self.base_stations = []
        self.user_equipments = []

        self.action_space = spaces.Discrete(2)
        
        self.observation_space = spaces.Box(low=np.array([-np.inf, 0, 0, 0, 0]),
                                            high=np.array([np.inf, 6000, 6000, 6000, 6000]),
                                            dtype=np.float32)

        self.current_ue_index = 0
        self.reset()

    def reset(self):
        self.base_stations.clear()  
        self.user_equipments.clear()  
        self.init_simulation()  
        return self.get_state()

    def init_simulation(self):
        num_base_stations = 5  
        num_squares_per_bs = 20

        for i in range(num_base_stations):
            x = random.randint(100, 3000)
            y = random.randint(100, 3000)
            base_station = BaseStation(x, y)
            base_station.add_squares(num_squares_per_bs)
            self.base_stations.append(base_station)

        for bs in self.base_stations:
            for i in range(1):
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
        
    
        throughput = ue.throughput
        reward = self.calculate_reward(throughput)

        next_state = self.get_state()
        done = self.check_done() 
        return next_state, reward, done, {}

    def handle_handover(self, ue):
        current_bs = ue.serving_bs
        best_bs = max(self.base_stations, key=lambda bs: bs.signal_strength(ue), default=None)
        if best_bs and best_bs != current_bs:
            ue.serving_bs = best_bs
            ue.handover_occurred = True

    def calculate_reward(self, throughput):
        return throughput

    def check_done(self):
    
        return self.current_ue_index >= len(self.user_equipments) - 1

    def step_next_ue(self):
    
        self.current_ue_index = (self.current_ue_index + 1) % len(self.user_equipments)
