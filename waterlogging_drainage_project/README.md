# Waterlogging Drainage Strategy Evaluation

A traffic simulation project for evaluating waterlogging drainage strategies using SUMO (Simulation of Urban MObility).

## Project Overview

This project evaluates different drainage strategies for waterlogging points in urban road networks. It uses SUMO traffic simulation to compare the effectiveness of various drainage prioritization strategies based on:
- **Cumulative Throughput**: Total vehicles leaving waterlogging regions
- **Queue Length**: Average vehicles stuck in waterlogging areas
- **Average Speed**: Speed in waterlogging areas

## Features

- **Strategy Generation**: Generate optimal and worst-case drainage sequences based on traffic flow
- **Traffic Simulation**: Simulate waterlogging effects with adjustable speed reductions
- **Performance Evaluation**: Compare strategies at multiple time delays (30s, 60s, 120s)
- **Visualization**: 
  - Road network maps with waterlogging points highlighted
  - Comparison charts for different strategies
  - Detailed performance reports

## Project Structure

```
waterlogging_drainage_project/
├── config.json                          # Main configuration file
├── README.md                            # This file
├── requirements.txt                     # Python dependencies
├── data/                                # SUMO simulation data
│   ├── network/
│   │   └── new_add_light.net.xml       # Road network file
│   ├── routes/
│   │   └── mapall_addline_expand.rou.xml  # Vehicle routes
│   └── Core_500m_test.sumocfg          # SUMO configuration
├── src/                                 # Source code
│   ├── main.py                         # Main pipeline
│   ├── generate_strategy.py           # Strategy generation
│   ├── evaluate_strategy.py           # SUMO simulation & evaluation
│   ├── compare_strategies.py          # Strategy comparison
│   └── visualize_waterlogging.py      # Visualization tools
├── results/                            # Output directory (auto-generated)
│   ├── strategies_*/                   # Strategy files & evaluations
│   └── comparison_*/                   # Comparison reports & charts
└── waterlogging_point_identification/ # Waterlogging point data
    ├── waterlogging.py                # Point identification script
    ├── raw_data_V2.xlsx               # Raw data
    └── 武汉内涝点V1.0_四位小数.xlsx   # Wuhan waterlogging points
```

## Prerequisites

- **Python**: 3.8+
- **SUMO**: 1.15+ (with TraCI)
- **Python Packages**: See `requirements.txt`

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd waterlogging_drainage_project
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install SUMO:
   - Download from: https://sumo.dlr.de/docs/Downloads.php
   - Add SUMO_HOME environment variable
   - Ensure `sumo` is in your PATH

## Configuration

Edit `config.json` to customize:

### Network Files
```json
"network": {
  "net_file": "data/network/new_add_light.net.xml",
  "route_file": "data/routes/mapall_addline_expand.rou.xml"
}
```

### Simulation Parameters
```json
"sumo_config": {
  "simulation_steps": 200,              # Total simulation time
  "evaluation_delays": [30, 60, 120],   # Evaluation points (steps)
  "measurement_window": 200             # Measurement window (seconds)
}
```

### Waterlogging Points
```json
"waterlogging_points": {
  "g1": ["200040454", "200041869", ...],  # Edge IDs
  "g2": [...],
  ...
}
```

### Drainage Parameters
```json
"drainage_parameters": {
  "max_clean_at_once": 3,    # Max groups to drain per batch
  "steps_to_clean_one": 600,  # Time to drain one group
  "flooded_speed": 1.5,       # Speed in flooded areas (m/s)
  "normal_speed": 15          # Normal speed (m/s)
}
```

## Usage

### Run Complete Pipeline

From the project root directory:

```bash
python run_pipeline.py
```

This will:
1. Generate best and worst drainage strategies
2. Evaluate each strategy with SUMO simulation
3. Compare strategies and generate reports

### Individual Components

**Generate Strategies:**
```bash
cd src
python generate_strategy.py
```

**Evaluate a Strategy:**
```bash
cd src
python evaluate_strategy.py -s <strategy_file.json>
```

**Compare Two Strategies:**
```bash
cd src
python compare_strategies.py <eval1.json> <eval2.json>
```

**Visualize Waterlogging Points:**
```bash
cd src
python visualize_waterlogging.py
```

## Output

### Strategy Files
- `results/strategies_<timestamp>/best_strategy.json`: Optimal drainage order (high traffic → low)
- `results/strategies_<timestamp>/worst_strategy.json`: Worst-case order (low traffic → high)

### Evaluation Results
- `results/strategies_<timestamp>/evaluation_best.json`: Performance metrics for best strategy
- `results/strategies_<timestamp>/evaluation_worst.json`: Performance metrics for worst strategy

### Comparison Reports
- `results/comparison_<timestamp>/comparison_report.txt`: Detailed text report
- `results/comparison_<timestamp>/comparison_chart.png`: Performance charts
- `results/comparison_<timestamp>/comparison_report.json`: Structured comparison data

### Visualization
- `results/waterlogging_map.png`: Full network with waterlogging points
- `results/waterlogging_map_zoom_g*.png`: Individual group close-ups

## Metrics Explanation

### Cumulative Throughput
Total number of vehicles that **leave** the waterlogging region (not just change lanes internally). Higher values indicate better traffic flow.

### Queue Length
Average number of vehicles stuck in waterlogging areas at any given time. Lower values indicate less congestion.

### Average Speed
Mean speed of vehicles in waterlogging areas. Higher values indicate less impact from flooding.

## Example Results

```
Batch     Strategy       Drained     Cumulative     Queue          Speed(m/s)
1         best           3           681            814.36         1.967
1         worst          3           502            836.75         1.566
2         best           6           932            685.82         3.552
2         worst          6           777            709.51         3.065
```

**Best Strategy** shows:
- +35.7% more throughput in Batch 1
- -2.7% fewer vehicles in queue
- +25.6% higher average speed

## Waterlogging Point Identification

The `waterlogging_point_identification/` folder contains:
- Historical waterlogging data for Wuhan
- Scripts to identify and map waterlogging points to road network edges
- Visualization of waterlogging point distribution

See `waterlogging_point_identification/README.md` for details.

## Customization

### Adding New Waterlogging Groups
1. Identify edge IDs from your network file
2. Add to `config.json` under `waterlogging_points`
3. Run the pipeline

### Adjusting Drainage Constraints
Modify `drainage_parameters` in `config.json`:
- `max_clean_at_once`: Resource constraint (e.g., number of teams)
- `steps_to_clean_one`: Time required per group
- `flooded_speed`: Impact on vehicle speed

### Custom Strategies
Create your own strategy JSON file:
```json
{
  "name": "custom_strategy",
  "drainage_batches": [
    ["g1", "g2", "g3"],
    ["g4", "g5", "g6"],
    ["g7", "g8", "g9"]
  ]
}
```

Then evaluate with:
```bash
python evaluate_strategy.py custom_strategy.json
```

## Troubleshooting

**SUMO not found:**
- Set SUMO_HOME environment variable
- Verify `sumo` command works in terminal

**Network file errors:**
- Check paths in `config.json` are correct
- Ensure network and route files are compatible

**Simulation crashes:**
- Reduce `simulation_steps` for testing
- Check waterlogging edge IDs exist in network

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

[Add your license here]

## Citation

If you use this code in your research, please cite:

```
[Add citation information]
```

## Contact

[Add contact information]

## Acknowledgments

- SUMO traffic simulation framework: https://sumo.dlr.de/
- [Add other acknowledgments]
