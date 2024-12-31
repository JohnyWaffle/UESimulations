import numpy as np

class BaseStation:
    def __init__(self, x, y, tx_power=46):
        self.x = x
        self.y = y
        self.tx_power = tx_power
        self.radius = 1000 
        self.squares = []

    def signal_strength(self, ue):
        distance = np.hypot(self.x - ue.x, self.y - ue.y)
        path_loss = 128.1 + 37.6 * np.log10(max(distance / 1000, 1e-6))
        return self.tx_power - path_loss

    def get_distance(self, ue):
        return np.hypot(self.x - ue.x, self.y - ue.y)

    def add_squares(self, num_squares, square_size=50):
        while len(self.squares) < num_squares:
            rand_x = np.random.randint(self.x - self.radius, self.x + self.radius - square_size)
            rand_y = np.random.randint(self.y - self.radius, self.y + self.radius - square_size)
            if not self.check_overlap(rand_x, rand_y, square_size):
                self.squares.append((rand_x, rand_y))  

    def check_overlap(self, x, y, size):
        for square in self.squares:
            square_x, square_y = square
            if (x < square_x + size and x + size > square_x and
                y < square_y + size and y + size > square_y):
                return True  
        return False 
