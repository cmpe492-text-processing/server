import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from typing_extensions import deprecated


class Network:
    def __init__(self):
        self.graph = nx.Graph()
        self.nodes: list[tuple[int, str, float]] = []
        self.edges: list[tuple[int, int, int, float]] = []

    def add_node(self, wiki_id: int, entity_title: str, sentiment: float):
        node = (wiki_id, entity_title, sentiment)
        self.nodes.append(node)
        self.graph.add_node(wiki_id, entity_title=entity_title, sentiment=sentiment)

    def add_edge(self, entity1: int, entity2: int, edge_thickness: int, edge_weight: float):
        edge = (entity1, entity2, edge_thickness, edge_weight)
        self.edges.append(edge)
        self.graph.add_edge(entity1, entity2, edge_thickness=edge_thickness, edge_weight=edge_weight)

    def draw(self):
        # Color map for nodes based on sentiment
        cmap = mcolors.LinearSegmentedColormap.from_list("rg", ["red", "green"], N=256)
        sentiments = [data['sentiment'] for _, data in self.graph.nodes(data=True)]
        norm = mcolors.Normalize(vmin=0, vmax=1)
        color_map = [cmap(norm(sentiment)) for sentiment in sentiments]

        # Positions for all nodes using a layout that considers edge weight
        pos = nx.spring_layout(self.graph, weight='weight')  # Use the 'weight' attribute to influence the layout

        # Drawing the nodes
        nx.draw_networkx_nodes(self.graph, pos, node_color=color_map, node_size=5)

        # Drawing the edges with variable thickness based on 'edge_thickness' attribute
        edge_widths = [self.graph[u][v].get('edge_thickness', 1.0) for u, v in self.graph.edges()]
        nx.draw_networkx_edges(self.graph, pos, width=edge_widths, alpha=0.5)

        # Labels for the nodes
        labels = {node: data['entity_title'] for node, data in self.graph.nodes(data=True)}
        nx.draw_networkx_labels(self.graph, pos, labels=labels, font_size=1)

        plt.axis('off')
        plt.show()

    def export_gephi(self):
        nx.write_gexf(self.graph, "../../resources/gephi/export/trump.gexf")

    def degree_centrality(self):
        return nx.degree_centrality(self.graph)

    def communities(self):
        return nx.algorithms.community.greedy_modularity_communities(self.graph)

    def shortest_path(self, source: int, target: int):
        return nx.shortest_path(self.graph, source, target)

    def import_csv(self, path):
        # Import nodes
        with open(path + '/nodes.csv', 'r') as f:
            for line in f:
                line = line.strip().split(',')
                self.add_node(int(line[0]), line[1], float(line[2]))

        # Import edges
        with open(path + '/edges.csv', 'r') as f:
            for line in f:
                line = line.strip().split(',')
                self.add_edge(int(line[0]), int(line[1]), int(line[2]), float(line[3]))


"""
        node: entity
        node: color (graph icindeki communitysine ait renk) 
        node: total sentiment - 
        
        edge:   entity1, entity2, 
                edge_thickness: co-occurences, 
                edge_force: relatedness, (pull force)
        
        EDGE_WEIGHT = EDGE_FORCE ... same thing 
"""
