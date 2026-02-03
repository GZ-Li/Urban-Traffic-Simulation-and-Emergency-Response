"""
Visualize waterlogging points on the road network map
"""

import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import json
from matplotlib.patches import Rectangle
from matplotlib.collections import LineCollection
import numpy as np

def load_config(config_file='config.json'):
    """Load configuration file"""
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_network(net_file):
    """Load SUMO network and extract edge coordinates"""
    tree = ET.parse(net_file)
    root = tree.getroot()
    
    edges = {}
    junctions = {}
    
    # Load junctions
    for junction in root.findall('junction'):
        junc_id = junction.get('id')
        x = float(junction.get('x'))
        y = float(junction.get('y'))
        junctions[junc_id] = (x, y)
    
    # Load edges and lanes
    for edge in root.findall('edge'):
        edge_id = edge.get('id')
        from_junc = edge.get('from')
        to_junc = edge.get('to')
        
        # Get lane coordinates
        lanes = []
        for lane in edge.findall('lane'):
            lane_id = lane.get('id')
            shape = lane.get('shape')
            if shape:
                # Parse shape coordinates
                coords = []
                for point in shape.split():
                    x, y = point.split(',')
                    coords.append((float(x), float(y)))
                lanes.append({
                    'id': lane_id,
                    'coords': coords
                })
        
        if lanes:
            edges[edge_id] = {
                'from': from_junc,
                'to': to_junc,
                'lanes': lanes
            }
    
    return edges, junctions

def get_lane_to_edge_mapping(edges):
    """Create mapping from lane ID to edge ID"""
    lane_to_edge = {}
    for edge_id, edge_data in edges.items():
        for lane in edge_data['lanes']:
            lane_id = lane['id']
            lane_to_edge[lane_id] = edge_id
    return lane_to_edge

def plot_network_with_waterlogging(config, output_file='waterlogging_map.png'):
    """Plot road network with waterlogging points highlighted"""
    
    print("Loading network...")
    edges, junctions = load_network(config['network']['net_file'])
    lane_to_edge = get_lane_to_edge_mapping(edges)
    
    # Get waterlogging groups
    waterlogging_groups = config['waterlogging_points']
    
    # Create figure
    fig, ax = plt.subplots(figsize=(20, 20))
    
    # Use single red color for all waterlogging groups
    waterlogging_color = 'red'
    
    # Plot all edges (normal roads in gray)
    print("Plotting road network...")
    for edge_id, edge_data in edges.items():
        for lane in edge_data['lanes']:
            coords = lane['coords']
            if len(coords) >= 2:
                x_coords = [c[0] for c in coords]
                y_coords = [c[1] for c in coords]
                ax.plot(x_coords, y_coords, 'gray', linewidth=0.5, alpha=0.3)
    
    # Plot waterlogging lanes (highlighted)
    print("Highlighting waterlogging areas...")
    print(f"Total edges in network: {len(edges)}")
    print(f"Total lanes mapped: {len(lane_to_edge)}")
    
    waterlogging_edges = set()
    legend_handles = []
    group_centers = {}  # Store centers for labeling
    
    for group_name, lane_ids in sorted(waterlogging_groups.items()):
        group_coords = []
        print(f"\nProcessing group {group_name} with {len(lane_ids)} edge IDs...")
        
        for edge_id in lane_ids:  # These are actually edge IDs, not lane IDs
            if edge_id not in edges:
                print(f"  WARNING: Edge {edge_id} not found in network")
                continue
                
            waterlogging_edges.add(edge_id)
            edge_data = edges[edge_id]
            
            # Plot all lanes of this edge
            for lane in edge_data['lanes']:
                coords = lane['coords']
                if len(coords) >= 2:
                    x_coords = [c[0] for c in coords]
                    y_coords = [c[1] for c in coords]
                    
                    # Plot with thick red line
                    line, = ax.plot(x_coords, y_coords, color=waterlogging_color, 
                                  linewidth=3, alpha=0.7, label=group_name, zorder=2)
                    group_coords.extend(coords)
            
            print(f"  Found edge {edge_id}: {len(edge_data['lanes'])} lanes")
        
        # Calculate center and store for later
        if group_coords:
            center_x = sum(c[0] for c in group_coords) / len(group_coords)
            center_y = sum(c[1] for c in group_coords) / len(group_coords)
            group_centers[group_name] = (center_x, center_y)
            print(f"  Group {group_name}: {len(group_coords)} coords, center=({center_x:.1f}, {center_y:.1f})")
    
    print(f"\nTotal groups with centers: {len(group_centers)}")
    
    # Set labels and title
    ax.set_xlabel('X Coordinate (m)', fontsize=14)
    ax.set_ylabel('Y Coordinate (m)', fontsize=14)
    ax.set_title('Waterlogging Points Distribution on Road Network', 
                fontsize=16, fontweight='bold', pad=20)
    
    # Grid
    ax.grid(True, alpha=0.2)
    ax.set_aspect('equal')
    
    # Add summary text
    total_edges = sum(len(edges) for edges in waterlogging_groups.values())
    summary_text = f'Waterlogging Areas: {len(waterlogging_groups)} groups ({total_edges} edges)'
    ax.text(0.02, 0.98, summary_text, transform=ax.transAxes,
           fontsize=12, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='white', edgecolor='red', linewidth=2, alpha=0.9))
    
    # Save figure
    plt.tight_layout()
    plt.savefig(output_file, dpi=200, bbox_inches='tight')
    print(f"\nMap saved to: {output_file}")
    
    # Also create a zoomed version for each group
    print("\nGenerating individual group visualizations...")
    for group_name, edge_ids in sorted(waterlogging_groups.items()):
        fig_zoom, ax_zoom = plt.subplots(figsize=(12, 12))
        
        # Collect coordinates for this group
        group_x, group_y = [], []
        for edge_id in edge_ids:
            if edge_id in edges:
                edge_data = edges[edge_id]
                for lane in edge_data['lanes']:
                    coords = lane['coords']
                    for x, y in coords:
                        group_x.append(x)
                        group_y.append(y)
        
        if not group_x:
            plt.close(fig_zoom)
            continue
        
        # Calculate bounds with margin
        margin = 200  # 200m margin
        x_min, x_max = min(group_x) - margin, max(group_x) + margin
        y_min, y_max = min(group_y) - margin, max(group_y) + margin
        
        # Plot nearby edges
        for edge_id, edge_data in edges.items():
            for lane in edge_data['lanes']:
                coords = lane['coords']
                if len(coords) >= 2:
                    x_coords = [c[0] for c in coords]
                    y_coords = [c[1] for c in coords]
                    
                    # Check if edge is in view
                    if (min(x_coords) <= x_max and max(x_coords) >= x_min and
                        min(y_coords) <= y_max and max(y_coords) >= y_min):
                        
                        # Check if this edge belongs to waterlogging group
                        is_waterlogged = False
                        for eid in edge_ids:
                            if edge_id == eid:
                                is_waterlogged = True
                                break
                        
                        if is_waterlogged:
                            # Highlight waterlogging lane
                            ax_zoom.plot(x_coords, y_coords, color='red', 
                                       linewidth=4, alpha=0.8, zorder=3)
                        else:
                            # Normal road
                            ax_zoom.plot(x_coords, y_coords, 'gray', linewidth=1, alpha=0.4)
        
        ax_zoom.set_xlim(x_min, x_max)
        ax_zoom.set_ylim(y_min, y_max)
        ax_zoom.set_xlabel('X Coordinate (m)', fontsize=12)
        ax_zoom.set_ylabel('Y Coordinate (m)', fontsize=12)
        ax_zoom.set_title(f'Waterlogging Group: {group_name}', 
                         fontsize=14, fontweight='bold')
        ax_zoom.grid(True, alpha=0.3)
        ax_zoom.set_aspect('equal')
        
        # Add edge list
        edge_text = f'Edges: {', '.join(edge_ids[:5])}'
        if len(edge_ids) > 5:
            edge_text += f'\n... and {len(edge_ids)-5} more'
        ax_zoom.text(0.02, 0.98, edge_text, transform=ax_zoom.transAxes,
                    fontsize=10, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='white', edgecolor='red', linewidth=1.5, alpha=0.9))
        
        zoom_file = output_file.replace('.png', f'_zoom_{group_name}.png')
        plt.tight_layout()
        plt.savefig(zoom_file, dpi=150, bbox_inches='tight')
        plt.close(fig_zoom)
        print(f"  - {group_name}: {zoom_file}")
    
    plt.show()

if __name__ == '__main__':
    print("="*80)
    print("  Waterlogging Points Visualization")
    print("="*80)
    
    config = load_config()
    plot_network_with_waterlogging(config, 'results/waterlogging_map.png')
    
    print("\n" + "="*80)
    print("  Visualization completed!")
    print("="*80)
