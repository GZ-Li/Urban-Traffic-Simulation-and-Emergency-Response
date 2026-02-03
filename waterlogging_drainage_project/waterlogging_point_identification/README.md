# Waterlogging Point Identification

This folder contains data and scripts for identifying waterlogging points in Wuhan's road network.

## Files

- **waterlogging.py**: Script to process and map waterlogging points to road network edges
- **raw_data_V2.xlsx**: Raw waterlogging event data
- **武汉内涝点V1.0_四位小数.xlsx**: Processed Wuhan waterlogging points with coordinates
- **内涝点.png**: Visualization of waterlogging point distribution

## Usage

This data is used to configure the waterlogging points in the main project's `config.json` file.

The identified edge IDs are mapped to the 9 waterlogging groups (g1-g9) used in the simulation.

## Data Source

Historical waterlogging data from Wuhan urban area, processed to map to SUMO road network edge IDs.
