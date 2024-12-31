import pyqtgraph as pg
from collections import deque
import numpy as np
import csv
import os

class SINRPlot(pg.PlotWidget):
    def __init__(self, title, num_base_stations, height=200):
        super().__init__()
        self.setTitle(title)
        self.setBackground('w')
        self.setMinimumHeight(height) 
        self.sinr_curves = {}
        self.sinr_data = {}
        self.handover_lines = [] 
        self.cur_min_time_step = None
        self.cur_min_value = float('inf')
        for bs_id in range(num_base_stations):
            color = (50 * bs_id) % 255
            self.sinr_curves[bs_id] = self.plot(pen={'color': (color, 0, 255 - color), 'width': 2}, name=f"BS {bs_id + 1} SINR")
            self.sinr_data[bs_id] = deque(maxlen=30000)

    def update_plot(self, ue, base_stations, time_step):
        interference = np.average([b.signal_strength(ue) for b in base_stations if b != ue.serving_bs])
        P_signal = 10 ** (ue.serving_bs.signal_strength(ue) / 10)
        P_interference = 10 ** (interference / 10)
        P_noise = 10 ** (ue.noise / 10)
        SINR_linear = P_signal / (P_interference + P_noise)
        sinr = 10 * np.log10(SINR_linear)
        self.sinr_data[0].append(sinr)
        self.sinr_curves[0].setData(list(self.sinr_data[0]))
        if sinr < self.cur_min_value:
            self.cur_min_value = sinr
            self.cur_min_time_step = time_step
        if ue.handover_occurred:
            self.add_handover_lines(time_step)

    def add_handover_lines(self, time_step):
        t_predicted = time_step - 30  
        t_actual = time_step 
        t_latency = t_actual + 30  
       
        predicted_line = pg.InfiniteLine(pos=t_predicted, angle=90, pen={'color': 'blue', 'style': pg.QtCore.Qt.PenStyle.DashLine})
        actual_line = pg.InfiniteLine(pos=t_actual, angle=90, pen={'color': 'orange', 'style': pg.QtCore.Qt.PenStyle.SolidLine})
        latency_line = pg.InfiniteLine(pos=t_latency, angle=90, pen={'color': 'red', 'style': pg.QtCore.Qt.PenStyle.DashDotLine})
        self.addItem(predicted_line)
        self.addItem(actual_line)
        self.addItem(latency_line)
        self.handover_lines.append((predicted_line, actual_line, latency_line))

class ThroughputPlot(pg.PlotWidget):
    def __init__(self, title, num_base_stations, height=200):
        super().__init__()
        self.setTitle(title)
        self.setBackground('w')
        self.setMinimumHeight(height)  
        self.throughput_curves = {}
        self.throughput_data = {}
        self.handover_lines = []  
        self.cur_min_time_step = None
        self.cur_min_value = float('inf')
        self.cur_max_value = 0
        self.actual = 0
        self.latency = 0
        self.index = 0
        self.max_len = 30040
        self.prb = [0] * self.max_len  
        self.throughput_data[0] = [0] * self.max_len
        for bs_id in range(num_base_stations):
            color = (51 * bs_id) % 255
            self.throughput_curves[bs_id] = self.plot(pen={'color': (color, 255 - color, 0), 'width': 2}, name=f"BS {bs_id + 1} Throughput")
            self.throughput_data[bs_id] = deque(maxlen=30000)

    def update_plot(self, ue, base_stations, time_step, index):
        signal_strength = ue.serving_bs.signal_strength(ue)
        interference = sum([b.signal_strength(ue) for b in base_stations if b != ue.serving_bs])
        
        P_signal = 10 ** (signal_strength / 10)
        P_interference = 10 ** (interference / 10)
        P_noise = 10 ** (ue.noise / 10)
        SINR_linear = P_signal / (P_interference + P_noise)
        sinr = 10 * np.log10(SINR_linear)

        
        current_throughput = ue.bandwidth * np.log2(1 + 10 ** (10 * np.log10(SINR_linear) / 10))
        if time_step >= self.actual and time_step <= self.latency:
            current_throughput = 0
        self.throughput_data[0].append(current_throughput)
        self.throughput_curves[0].setData(list(self.throughput_data[0]))
        
        if current_throughput < self.cur_min_value:
            self.cur_min_value = current_throughput
            self.cur_min_time_step = time_step
            
        if current_throughput > self.cur_max_value:
            self.cur_max_value = current_throughput    
            
        current_packet_loss = self.calculate_packet_loss(sinr, ue.dynamic_prb)
        current_energy_consumption = self.calculate_energy_consumption(current_throughput)
        current_latency = self.calculate_latency(ue, ue.dynamic_prb)
        
        if ue.handover_occurred:
            self.add_handover_lines(time_step,sinr, ue.dynamic_prb,index)
            self.write_handover_to_csv(index,"Dynamic",time_step,current_latency,current_packet_loss,current_throughput,current_energy_consumption)
        else : 
            self.write_handover_to_csv(index,"Normal",time_step,current_latency,current_packet_loss,current_throughput,current_energy_consumption)

    def add_handover_lines(self, time_step, sinr, flag, index):
        t_predicted = time_step - 30  
        t_actual = time_step          
        t_latency = t_actual + 30     
        target_throughput_requirement = (self.cur_min_value + self.cur_max_value )/2
        bandwidth_per_prb = 20
        required_prbs = (target_throughput_requirement // bandwidth_per_prb) + (1 if target_throughput_requirement % bandwidth_per_prb != 0 else 0)
        if required_prbs != 0.0:
            self.write_PRB_to_csv(index, time_step, 25+required_prbs)
        if t_predicted > 0 and flag:        
            for i in range(t_predicted, t_actual):
                if i - 1 >= 0 and i - 1 < len(self.throughput_data[0]):  
                    if self.throughput_data[0][i-1] < target_throughput_requirement:
                        delta_n = (target_throughput_requirement - self.throughput_data[0][i-1]) / (bandwidth_per_prb * np.log2(1 + sinr))
                        self.prb[i-1] = delta_n
                        self.throughput_data[0][i-1] =self.throughput_data[0][i-1] + self.prb[i-1]

                        if self.throughput_data[0][i-1] < self.cur_min_value:
                            self.cur_min_value = self.throughput_data[0][i-1]
                            self.cur_min_time_step = time_step
                            
            for i in range(1,t_predicted):
                self.throughput_data[0][i-1] =self.throughput_data[0][i-1] - self.prb[i-1]
                
        self.actual = t_actual
        self.latency = t_latency
     
        for i in range (t_actual+1, t_latency):
            if i - 1 >= 0 and i - 1 < len(self.throughput_data[0]):  
                self.throughput_data[0][i-1] = 0
                
        predicted_line = pg.InfiniteLine(pos=t_predicted, angle=90,
                                          pen={'color': 'blue', 'style': pg.QtCore.Qt.PenStyle.DashLine})
        actual_line = pg.InfiniteLine(pos=t_actual, angle=90,
                                       pen={'color': 'orange', 'style': pg.QtCore.Qt.PenStyle.SolidLine})
        latency_line = pg.InfiniteLine(pos=t_latency, angle=90,
                                       pen={'color': 'red', 'style': pg.QtCore.Qt.PenStyle.DashDotLine})

        self.addItem(predicted_line)
        self.addItem(actual_line)
        self.addItem(latency_line)
        
        self.handover_lines.append((predicted_line, actual_line, latency_line))

    def calculate_latency(self, ue, flag):
        distance = ue.serving_bs.get_distance(ue)
        bandwidth = 40 if flag else ue.bandwidth + np.random.uniform(5, 10)
        speed_of_light = 3 * 10**8  
        propagation_delay = distance / speed_of_light  
        packet_size_bits = 1500 * 8 
        transmission_delay = packet_size_bits / bandwidth  
        return propagation_delay + transmission_delay  

    def calculate_packet_loss(self, sinr, flag):
        threshold_good = 20 
        threshold_bad = 10  
        if sinr >= threshold_good:
            return 0.0
        elif sinr < threshold_bad:
            return np.random.uniform(2, 4) if flag else 2  
        else:
            return np.random.uniform(1, 2) if flag else 1  

    def calculate_energy_consumption(self, throughput):
        power_per_data_unit = 0.01 
        return power_per_data_unit * throughput  

    def write_PRB_to_csv(self, index, time, PRB):
        output_file = 'out_prb.csv'   
        file_exists = os.path.isfile(output_file)

        last_entry = None

        if file_exists:
            with open(output_file, mode='r', newline='') as f:
                reader = csv.reader(f)
                rows = list(reader)
                if len(rows) > 1:  
                    last_entry = tuple(map(lambda x: int(x) if x.isdigit() else float(x) if x.replace('.', '', 1).isdigit() else x, rows[-1]))

        new_entry = (index, time, PRB)

        if last_entry is None or new_entry != last_entry:
            with open(output_file, mode='a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["Index", "Time", "PRB"])
                writer.writerow(new_entry)
  
    def write_handover_to_csv(self, index, method, time, latency, packet_loss, Throughput, Energy_Consumption):
        
        output_file = 'out_log.csv'   
        file_exists = os.path.isfile(output_file)
        last_entry = None
        
        if file_exists:
            with open(output_file, mode='r', newline='') as f:
                reader = csv.reader(f)
                rows = list(reader)
                last_entry = None
                if len(rows) > 1:  
                    last_entry = tuple(map(lambda x: int(x) if x.isdigit() else float(x) if x.replace('.', '', 1).isdigit() else x, rows[-1]))

        new_entry = (index, method, time, latency, packet_loss, Throughput, Energy_Consumption)

        if last_entry is None or new_entry != last_entry:
            with open(output_file, mode='a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["Index", "Method", "Time", "Latency", "Packet_Loss", "Throughput", "Energy_Consumption"])
                writer.writerow(new_entry)
