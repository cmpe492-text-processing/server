import os

from dotenv import load_dotenv
from graph.network import Network


if __name__ == "__main__":
    load_dotenv("../../.env")

    network = Network()
    """
        with open("{}nodes.csv".format(prefix), "w") as f:
            f.write("wiki_id,entity_title,sentiment\n")

        with open("{}edges.csv".format(prefix), "w") as f:
            f.write("entity1,entity2,edge_thickness,edge_weight\n")
    """

    with open("resources/data/graph/4848272_nodes.csv") as f:
        for line in f:
            if line.startswith("wiki_id"):
                continue
            line = line.strip().split(",")
            network.add_node(int(line[0]), line[1], float(line[2]))

    with open("resources/data/graph/4848272_edges.csv") as f:
        for line in f:
            if line.startswith("entity1"):
                continue
            line = line.strip().split(",")
            network.add_edge(int(line[0]), int(line[1]), int(line[2]), float(line[3]))

    print(network.degree_centrality())
    print(network.communities())
    network.export_gephi()
