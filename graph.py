import networkx as nx
import matplotlib.pyplot as pyplot
import csv


class Node():
    def __init__(self, node):
        self.name = node[0]
        self.lat = node[1]
        self.long = node[2]
        self.speed = node[3]
        self.capacity = node[4]
        self.speedPref = node[5]
        self.costPref = node[6]


class Network():
    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes = []

        with open('nodes.csv') as nodeFile:
            nodes = csv.reader(nodeFile)
            for n in nodes:
                node = Node(n)
                self.nodes.append((node.name, node))
                self.graph.add_node(node.name, node=node)

        with open('connections.csv') as connectionsFile:
            connections = csv.reader(connectionsFile)
            for c in connections:
                self.graph.add_edge(c[0], c[1])

    def draw(self):
        print(self.graph.nodes(data=True))
        nx.draw(self.graph)
        pyplot.show()


network = Network()
network.draw()
