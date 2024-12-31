import numpy as np
import random  

class UserEquipment:
    def __init__(self, x, y, target_x, target_y, bandwidth=20):
        self.x = x
        self.y = y
        self.target_x = target_x
        self.target_y = target_y
        self.bandwidth = bandwidth
        self.dynamic_prb = False  
        self.signal_strength = -100
        self.throughput = 0
        self.noise = -174 + 10 * np.log10(self.bandwidth * 1e6) + 9
        self.serving_bs = None
        self.handover_occurred = False

    def move(self):
        step_size = 1.2 
        target_direction_x = self.target_x - self.x
        target_direction_y = self.target_y - self.y
        distance = np.hypot(target_direction_x, target_direction_y)

        if distance > 0:
            dx = step_size * (target_direction_x / distance)  
            dy = step_size * (target_direction_y / distance)
            self.x = max(0, min(self.x + dx, 6000)) 
            self.y = max(0, min(self.y + dy, 6000))   

        if random.random() < 0.1: 
            self.target_x = random.randint(100, 900)  
            self.target_y = random.randint(100, 700)  

    def update_signal_strength(self, base_stations):
        best_bs = None
        best_sinr = -np.inf
        best_throughput = -np.inf

        for bs in base_stations:
            signal_strength = bs.signal_strength(self)
            interference = np.average([b.signal_strength(self) for b in base_stations if b != bs])

            P_signal = 10 ** (signal_strength / 10)
            P_interference = 10 ** (interference / 10)
            P_noise = 10 ** (self.noise / 10)
            SINR_linear = P_signal / (P_interference + P_noise)

            sinr = 10 * np.log10(SINR_linear)

            distance_to_bs = bs.get_distance(self)
            if distance_to_bs <= bs.radius:
                loss = random.choice([-2, -3, -4]) 
                sinr += loss

            adjusted_bandwidth = self.bandwidth + (10 if self.dynamic_prb else 0)
            throughput = adjusted_bandwidth * np.log2(1 + 10 ** (sinr / 10))

            min_required_throughput = 10 
            BW = self.bandwidth
            gamma_th = 2 ** (min_required_throughput / BW) - 1
            gamma = 2 ** (throughput / BW) - 1

            lambda_value = 0.01  
            P_failure = 1 - np.exp(-gamma_th / lambda_value * gamma)

            if sinr > best_sinr and P_failure > 0.5:
                best_bs = bs
                best_sinr = sinr
                best_throughput = throughput

        if best_bs and best_bs != self.serving_bs:
            if self.serving_bs is not None:
                self.handover_occurred = True
            self.serving_bs = best_bs

        self.signal_strength = self.serving_bs.signal_strength(self) if self.serving_bs else self.signal_strength
        self.throughput = best_throughput
