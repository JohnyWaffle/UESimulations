import csv
import random
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QScrollArea, QGroupBox, QPushButton, QSpacerItem, QSizePolicy
from PyQt6.QtCore import QTimer
from simulation.environment import Environment
from simulation.base_station import BaseStation
from simulation.user_equipment import UserEquipment
from simulation.rl_environment import MobileNetworkRLEnv  
from gui.network_view import NetworkView
from gui.plots import SINRPlot, ThroughputPlot

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Network Simulation")
        self.setGeometry(100, 100, 1600, 900)

        self.dynamic_metrics = {"latency": 0, "packet_loss": 0, "throughput": 0, "energy": 0}
        self.regular_metrics = {"latency": 0, "packet_loss": 0, "throughput": 0, "energy": 0}

        self.time_step = 0
        self.max_time_steps = 200
        
        self.env = MobileNetworkRLEnv() 
        self.init_simulation()

        layout = QHBoxLayout()
        self.network_view = NetworkView(self.env)
        self.network_view.setMaximumWidth(900) 
        layout.addWidget(self.network_view)
        button_layout = QVBoxLayout()
        self.create_movement_buttons(button_layout)
        layout.addLayout(button_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        right_widget = QWidget()  
        right_layout = QVBoxLayout(right_widget)

        self.ue_plots = []
        for ue in self.env.user_equipments:
            group_box = QGroupBox(f"UE {self.env.user_equipments.index(ue) + 1}")  
            plot_layout = QVBoxLayout()
            dynamic_sinr_plot = SINRPlot("Dynamic PRB SINR", 5, height=250)
            dynamic_throughput_plot = ThroughputPlot("Dynamic PRB Throughput", 5, height=250)
            normal_sinr_plot = SINRPlot("Regular PRB SINR", 5, height=250)
            normal_throughput_plot = ThroughputPlot("Regular Throughput", 5, height=250)
            plot_layout.addWidget(dynamic_sinr_plot)
            plot_layout.addWidget(dynamic_throughput_plot)
            plot_layout.addWidget(normal_sinr_plot)
            plot_layout.addWidget(normal_throughput_plot)
            group_box.setLayout(plot_layout)
            self.ue_plots.append((dynamic_sinr_plot, dynamic_throughput_plot, normal_sinr_plot, normal_throughput_plot))
            right_layout.addWidget(group_box)

        self.scroll_area.setWidget(right_widget)
        layout.addWidget(self.scroll_area)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_simulation)
        self.timer.start(100)

    def create_movement_buttons(self, layout):
        move_left_button = QPushButton("Left")
        move_left_button.clicked.connect(lambda: self.move_network_view(-100, 0)) 
        layout.addWidget(move_left_button)

        move_right_button = QPushButton("Right")
        move_right_button.clicked.connect(lambda: self.move_network_view(100, 0))  
        layout.addWidget(move_right_button)
        move_up_button = QPushButton("Up")
        move_up_button.clicked.connect(lambda: self.move_network_view(0, -100)) 
        layout.addWidget(move_up_button)
        move_down_button = QPushButton("Down")
        move_down_button.clicked.connect(lambda: self.move_network_view(0, 100))  
        layout.addWidget(move_down_button)
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding))

    def move_network_view(self, dx, dy):
        current_position = self.network_view.sceneRect()
        new_rect = current_position.adjusted(dx, dy, dx, dy)
        self.network_view.setSceneRect(new_rect)

    def init_simulation(self):
        self.env.reset() 
        
    def update_simulation(self):
        if self.time_step >= self.max_time_steps:
            self.timer.stop()
            print("Simulation ended after 100 seconds.")
            avg_dynamic_metrics = {key: value / self.max_time_steps for key, value in self.dynamic_metrics.items()}
            avg_regular_metrics = {key: value / self.max_time_steps for key, value in self.regular_metrics.items()}
            latency_reduction = abs(100 * (avg_dynamic_metrics["latency"] - avg_regular_metrics["latency"]) / avg_regular_metrics["latency"])
            packet_loss_reduction = abs(100 * (avg_dynamic_metrics["packet_loss"] - avg_regular_metrics["packet_loss"]) / avg_regular_metrics["packet_loss"])
            throughput_increase = abs(100 * (avg_dynamic_metrics["throughput"] - avg_regular_metrics["throughput"]) / avg_regular_metrics["throughput"])
            energy_savings = 100 * abs(avg_dynamic_metrics["energy"] - avg_regular_metrics["energy"]) / avg_regular_metrics["energy"]

            print("Dynamic PRB/Regular PRB:")
            print(f"Latency Reduction: {latency_reduction:.3f}% "
                  f"Packet Loss Reduction: {packet_loss_reduction:.3f}% "
                  f"Throughput Increase: {throughput_increase:.3f}% "
                  f"Energy Savings: {energy_savings:.3f}%")
            return

        self.env.step(random.choice([0, 1]))  
        self.network_view.update_scene()  
        self.calculate_metrics()
        self.time_step += 1

    def calculate_metrics(self):
        for ue_index, ue in enumerate(self.env.user_equipments):
            ue.dynamic_prb = True
            ue.update_signal_strength(self.env.base_stations)

            dynamic_sinr_plot, dynamic_throughput_plot, normal_sinr_plot, normal_throughput_plot = self.ue_plots[ue_index]
            dynamic_sinr_plot.update_plot(ue, self.env.base_stations, self.time_step)
            dynamic_throughput_plot.update_plot(ue, self.env.base_stations, self.time_step, ue_index)

            dynamic_latency = dynamic_throughput_plot.calculate_latency(ue, True)
            dynamic_packet_loss = dynamic_throughput_plot.calculate_packet_loss(ue.signal_strength, True)
            dynamic_energy = dynamic_throughput_plot.calculate_energy_consumption(ue.throughput)

            self.dynamic_metrics["latency"] += dynamic_latency
            self.dynamic_metrics["packet_loss"] += dynamic_packet_loss
            self.dynamic_metrics["throughput"] += ue.throughput
            self.dynamic_metrics["energy"] += dynamic_energy

            ue.dynamic_prb = False
            ue.update_signal_strength(self.env.base_stations)

            normal_sinr_plot.update_plot(ue, self.env.base_stations, self.time_step)
            normal_throughput_plot.update_plot(ue, self.env.base_stations, self.time_step, ue_index)

            normal_latency = normal_throughput_plot.calculate_latency(ue, False)
            normal_packet_loss = normal_throughput_plot.calculate_packet_loss(ue.signal_strength, False)
            normal_energy = normal_throughput_plot.calculate_energy_consumption(ue.throughput)

            self.regular_metrics["latency"] += normal_latency
            self.regular_metrics["packet_loss"] += normal_packet_loss
            self.regular_metrics["throughput"] += ue.throughput
            self.regular_metrics["energy"] += normal_energy

            ue.handover_occurred = False
