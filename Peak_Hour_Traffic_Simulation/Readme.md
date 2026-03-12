# Peak Hour Traffic Simulation Based on OD Matrix

A microscopic traffic flow generation system based on OD (Origin-Destination) matrices, mapping macroscopic traffic demand to microscopic vehicle generation parameters.

## Project Overview

This project generates realistic peak-hour traffic patterns by transforming macroscopic OD matrix data into microscopic vehicle trip data. Instead of uniform random sampling, it uses weighted sampling based on traffic flow to create more realistic traffic distributions.

## Features

- **OD Matrix Parsing**: Read inter-regional traffic flow demand matrices
- **Lane Mapping**: Establish correspondence between Traffic Analysis Zones (TAZ) and network lanes
- **Weighted Sampling**: Flow-weight-based random sampling, replacing uniform distribution
- **Microscopic Trajectory Generation**: Generate vehicle trips that conform to macroscopic OD characteristics

## Algorithm

### Weighted Sampling Approach

Replace the default uniform sampling probability with weighted sampling:

$$P_{weighted}(l_i) = \frac{w_i}{\sum_{j \in L} w_j}$$

Where $w_i$ is the lane flow weight derived from the OD matrix.

### Technical Implementation

- Modify `mosstool/trip/generator/random.py` `_rand_position` function
- Use `random.choices(lanes, weights=weights)` for weighted sampling
- High-flow regions' lanes are more likely to be selected as trip origins/destinations

## Project Structure

```
Peak_Hour_Traffic_Simulation/
├── README.md                     # This file
├── README_CN.md                  # Chinese documentation
└── docs/
    └── technical_design.md       # Detailed technical design document
```

## Current Status

- **Deployment Status**: Pending
- **Reason**: The current environment has not yet provided the complete OD data interface module
- **Plan**: The code injection approach has been drafted and will be deployed once the environment is updated

## Workflow Design

### Data Flow

```
OD Matrix (macroscopic)
    │
    ▼
TAZ-to-Lane Mapping
    │
    ▼
Lane Flow Weight Calculation
    │
    ▼
Weighted Random Sampling
    │
    ▼
Microscopic Vehicle Trips
```

### Integration Points

1. **Input**: OD matrix data from traffic survey or model
2. **Processing**: Weight calculation and sampling modification in `mosstool`
3. **Output**: Vehicle trip data compatible with SUMO/custom simulator

## Dependencies

- Python 3.8+
- mosstool (traffic simulation toolkit)
- numpy

## References

- OD Matrix theory and traffic demand modeling
- mosstool framework documentation
