class Environment:
    def __init__(self, grid_size=200):
        self.grid_size = grid_size
        self.base_stations = []
        self.user_equipments = []

    def add_base_station(self, base_station):
        self.base_stations.append(base_station)

    def add_user_equipment(self, ue):
        self.user_equipments.append(ue)

    def update(self):
        for ue in self.user_equipments:
            ue.move()
            ue.update_signal_strength(self.base_stations)
