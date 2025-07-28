import numpy as np
import sumolib
import networkx as nx
from collections import defaultdict

class MCTSNode:
    def __init__(self, name, parent = None, used_edges = None):
        self.name = name
        self.parent = parent
        self.used_edges = used_edges if used_edges else set()
        self.children = []
        self.total_reward = 0
        self.visits = 0


def netxml_to_networkx(net_file):
    net = sumolib.net.readNet(net_file)
    G = nx.DiGraph()
    for edge in net.getEdges():
        from_node = edge.getFromNode().getID()
        to_node = edge.getToNode().getID()
        edge_id = edge.getID()
        length = edge.getLength()
        G.add_edge(
            from_node,
            to_node,
            length=length,
            edge_id=edge.getID(),  # 原始edge的ID
        )
    return G


def expand(node, G, goal):
    if node.name == goal:
        return None
    neighbors = []
    for to_node in G.neighbors(node.name):
        edge_data = G.get_edge_data(node.name, to_node)
        sumo_edge_id = edge_data["edge_id"]
        if sumo_edge_id not in node.used_edges:
            neighbors.append((to_node, sumo_edge_id))
    if neighbors:
        to_node, sumo_edge_id = neighbors[np.random.randint(len(neighbors))]
        new_used_edges = set(node.used_edges)
        new_used_edges.add(sumo_edge_id)
        new_node = MCTSNode(to_node, parent=node, used_edges=new_used_edges)
        node.children.append(new_node)
        return new_node
    return None


if __name__ == "__main__":
    net_file = "E:\\Traffic_Simulation\\snowplow_routing\\net\\toy.net.xml"
    G = netxml_to_networkx(net_file)
    # print(f"节点数: {len(G.nodes())}")
    # print(f"边数: {len(G.edges())}")
    # for u, v, data in G.edges(data=True):
    #     print(f"边 {u} -> {v}: 车道ID={data['edge_id']}, 长度={data['length']}m")
    # print(expand(MCTSNode("J0"), G, MCTSNode("J10")).name)
    