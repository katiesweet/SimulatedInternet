import csv
import networkx as nx
import matplotlib.pyplot as pyplot
import PathFindingAlgorithm

MIN_MESSAGES_BEFORE_UPDATE = 2
DECREASE_THRESHOLD = 0.3
INCREASE_THRESHOLD = 0.7
DECREASE_AMOUNT = 0.1
INCREASE_AMOUNT = 0.05
MIN_PRICE = 0.1


class Node():
    def __init__(self, node):
        self.name = node[0]
        self.lat = float(node[1])
        self.long = float(node[2])
        self.speed = float(node[3])
        self.speedPref = float(node[5])
        self.costPref = float(node[6])
        self.costPerMByte = float(node[7])
        self.balance = 0
        self.numMessagesSent = 0
        self.numMessagesSeen = 0
        self.numMessagesTransmitted = 0
        self.messagesSeen = {}

    def createMessage(self, destination, size, content):
        self.numMessagesSent += 1
        message = Message(self.name,
                          destination,
                          self.speedPref,
                          self.costPref,
                          size,
                          content,
                          (self.name, self.numMessagesSent)
                          )
        return message

    def increasePrice(self):
        self.numMessageSeen = 0
        self.numMessagesTransmitted = 0
        self.costPerMByte += INCREASE_AMOUNT

    def decreasePrice(self):
        self.numMessageSeen = 0
        self.numMessagesTransmitted = 0
        self.costPerMByte = max(self.costPerMByte - DECREASE_AMOUNT, MIN_PRICE)


class Message():
    def __init__(self, startingNode, endingNode, speedPref, costPref, size, content, messageId):
        self.startingNode = startingNode
        self.endingNode = endingNode
        self.speedPref = speedPref
        self.costPref = costPref
        self.size = size
        self.content = content
        self.messageId = messageId


class Network():
    def __init__(self):
        self.graph = nx.Graph()
        self.algorithms = [PathFindingAlgorithm.AStarAlgorithm('A*'),
                           PathFindingAlgorithm.AgentApproach('Agent'),
                           PathFindingAlgorithm.AgentApproximation('Approximation')]

        with open('intrinsic.csv') as nodeFile:
            nodes = csv.reader(nodeFile)
            for n in nodes:
                node = Node(n)
                self.graph.add_node(node.name, node=node,
                                    pos=(node.long, node.lat))

        with open('connections.csv') as connectionsFile:
            connections = csv.reader(connectionsFile)
            for c in connections:
                self.graph.add_edge(c[0], c[1])

    def draw(self):
        pos = nx.get_node_attributes(self.graph, 'pos')
        nx.draw(self.graph, pos, with_labels=True)
        pyplot.show()

    def sendMessage(self, start, end, size, content):
        # print("\nSENDING MESSAGE FROM ", start, " TO ", end)
        for algorithm in self.algorithms:
            # print("\nUsing algorithm type: ", algorithm.name)
            startNode = self.graph.nodes[start]['node']
            message = startNode.createMessage(end, size, content)

            # Get path
            path = algorithm.getPath(self.graph, message)
            # print(path)

            if path:
                self.transmitMessageAndPayment(message, path)

    def transmitMessageAndPayment(self, message, remainingPath):
        if len(remainingPath) <= 0:
            print("ERROR!")

        # Handle your own payment
        currNode, currPayment = remainingPath[-1]
        actualNode = self.graph.node[currNode]['node']
        actualNode.balance += currPayment
        actualNode.numMessagesTransmitted += 1
        # print("Node ", currNode, " has a current balance of: ", actualNode.balance)

        if actualNode.numMessagesSeen > MIN_MESSAGES_BEFORE_UPDATE:
            transmissionRate = actualNode.numMessagesTransmitted / actualNode.numMessagesSeen

            if actualNode.costPerMByte != MIN_PRICE and transmissionRate < DECREASE_THRESHOLD:
                print("Decreasing from " + str(format(actualNode.costPerMByte, '.2f')) +
                      " to " + str(format(actualNode.costPerMByte - DECREASE_AMOUNT, '.2f')))
                actualNode.decreasePrice()
            elif transmissionRate > INCREASE_THRESHOLD:
                print("Increasing from " + str(format(actualNode.costPerMByte, '.2f')) +
                      " to " + str(format(actualNode.costPerMByte + INCREASE_AMOUNT, '.2f')))
                actualNode.increasePrice()

        # Remove yourself from the path
        remainingPath.pop()

        # If you are the receiver, report. Else, continue transmitting.
        if currNode != message.endingNode:
            # print("Node ", currNode, " received message: ", message.content)
            # else
            return self.transmitMessageAndPayment(message, remainingPath)


network = Network()

network.sendMessage('D', 'M', 1, "Hello!")
network.sendMessage('M', 'T', 2, "Hello 2!")
network.sendMessage('A', 'C', 1, "Hello!")
network.sendMessage('C', 'K', 1, "Hello!")
network.sendMessage('L', 'M', 1, "Hello!")
network.sendMessage('O', 'M', 1, "Hello!")
network.sendMessage('D', 'T', 1, "Hello!")
network.sendMessage('T', 'A', 1, "Hello!")
network.sendMessage('B', 'R', 1, "Hello!")
network.sendMessage('E', 'M', 1, "Hello!")
network.sendMessage('C', 'L', 1, "Hello!")
network.sendMessage('D', 'K', 1, "Hello!")
network.sendMessage('B', 'O', 1, "Hello!")
network.sendMessage('D', 'I', 1, "Hello!")
network.sendMessage('A', 'T', 1, "Hello!")
network.sendMessage('A', 'T', 1, "Hello!")
network.sendMessage('A', 'T', 1, "Hello!")
network.sendMessage('A', 'T', 1, "Hello!")
network.sendMessage('A', 'T', 1, "Hello!")
network.sendMessage('A', 'T', 1, "Hello!")
network.sendMessage('A', 'T', 1, "Hello!")
network.sendMessage('A', 'T', 1, "Hello!")
network.sendMessage('A', 'T', 1, "Hello!")
network.sendMessage('A', 'T', 1, "Hello!")
network.sendMessage('A', 'T', 1, "Hello!")
network.sendMessage('A', 'T', 1, "Hello!")
network.sendMessage('A', 'T', 1, "Hello!")

for nodeName in network.graph.nodes:
    node = network.graph.nodes[nodeName]['node']
    print(node.name + ": " + format(node.balance, '.2f'))

# network.draw()
