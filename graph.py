import networkx as nx
import matplotlib.pyplot as pyplot
import csv
import math
import copy
import PathFindingAlgorithm


class Node():
    def __init__(self, node):
        self.name = node[0]
        self.lat = float(node[1])
        self.long = float(node[2])
        self.speed = float(node[3])
        self.capacity = float(node[4])
        self.speedPref = float(node[5])
        self.costPref = float(node[6]) 
        self.costPerMByte = float(node[7])
        self.balance = 1000


class Message():
    def __init__(self, startingNode, endingNode, speedPref, costPref, size, content):
        self.startingNode = startingNode
        self.endingNode = endingNode
        self.speedPref = speedPref
        self.costPref = costPref
        self.size = size
        self.content = content


class Network():
    def __init__(self):
        self.graph = nx.Graph()
        self.algorithms = [PathFindingAlgorithm.AStarAlgorithm('A*'),
                           PathFindingAlgorithm.AgentApproach('Agent')]

        with open('Intrinsic.csv') as nodeFile:
            nodes = csv.reader(nodeFile)
            for n in nodes:
                node = Node(n)
                self.graph.add_node(node.name, node=node, pos=(node.long, node.lat))

        with open('connections.csv') as connectionsFile:
            connections = csv.reader(connectionsFile)
            for c in connections:
                self.graph.add_edge(c[0], c[1])

    def draw(self):
        pos = nx.get_node_attributes(self.graph, 'pos')
        nx.draw(self.graph, pos, with_labels=True)
        pyplot.show()

    def sendMessage(self, start, end, size, content):
        print("\nSENDING MESSAGE FROM ", start, " TO ", end)
        for algorithm in self.algorithms:
            print("\nUsing algorithm type: ", algorithm.name)
            startNode = self.graph.nodes[start]['node']
            message = Message(start,
                            end,
                            startNode.speedPref,
                            startNode.costPref,
                            size,
                            content)

            # Get path
            path = algorithm.getPath(self.graph, message)
            print(path)

            if path:
                self.transmitMessageAndPayment(message, path)

    def transmitMessageAndPayment(self, message, remainingPath):
        if len(remainingPath) <= 0:
            print("ERROR!")

        # Handle your own payment
        currNode, currPayment = remainingPath[-1]
        actualNode = self.graph.node[currNode]['node']
        actualNode.balance += currPayment
        print("Node ", currNode, " has a current balance of: ", actualNode.balance)

        # Remove yourself from the path
        remainingPath.pop()

        # If you are the receiver, report. Else, continue transmitting.
        if currNode == message.endingNode:
            print("Node ", currNode, " received message: ", message.content)
        else:
            return self.transmitMessageAndPayment(message, remainingPath)

network = Network()

network.sendMessage('D', 'M', 1, "Hello!")
network.sendMessage('M', 'T', 2, "Hello 2!")

network.draw()
