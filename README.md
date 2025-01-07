# UE Network Simulation, also with Reinforcement Learning

This is a PyQt6-based simulation of mobile networks featuring dynamic PRB allocation and reinforcement learning for handover optimization.

## Project Structure

### Core Components
- `main.py`: Entry point of the application
- `environment.py`: Base simulation environment
- `rl_environment.py`: RL implementation using PPO algorithm
- `user_equipment.py`: UE behavior and characteristics
- `base_station.py`: Base station properties and signal calculations

### GUI Components
- `main_window.py`: Main application window and simulation controller
- `network_view.py`: Visual representation of network elements
- `plots.py`: Real-time SINR and throughput plotting

## Key Configuration Parameters

### Simulation Settings
- Time duration: Modify `max_time_steps = 1000` in `main_window.py`
- Number of UEs: Adjust in `ue_size = 25 `in  `network_view.py`
- Number of base stations: Change `num_base_stations = 5` in `rl_environment.py`

### Network Parameters
- Base station radius: 1000m (modifiable in `base_station.py`)
- UE movement speed: 1.2 units/step (adjustable in `user_equipment.py`)
- Bandwidth: 20MHz default (configurable in `user_equipment.py`)

### Reinforcement Learning Configuration
- Algorithm: PPO (Proximal Policy Optimization)
- State space: 5 dimensions (SINR, x, y, target_x, target_y)
- Action space: Binary (0: no handover, 1: trigger handover)
- Training episodes: 1000 (configurable in `train_agent()`)

## Performance Metrics
- Dynamic vs Regular PRB allocation
- Latency reduction
- Packet loss
- Throughput improvement
- Energy consumption

## Output Files
- `out_log.csv`: Performance metrics log
- `out_prb.csv`: PRB allocation data

## Visualization
- Real-time network topology
- SINR plots
- Throughput graphs
- Handover indicators
