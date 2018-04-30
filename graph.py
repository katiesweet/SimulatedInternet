import csv
import networkx as nx
import matplotlib.pyplot as pyplot
import PathFindingAlgorithm
import datetime

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
    def __init__(self, algorithm, stats):
        self.graph = nx.Graph()
        self.algorithm = algorithm
        self.stats = stats

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
        print(self.graph.nodes)
        node_colors = [self.mapNodeColor(v) for v in self.graph.nodes()]
        nx.draw(self.graph, pos, with_labels=True, node_color=node_colors)
        pyplot.show()

    def mapNodeColor(self, node):
        n = self.graph.node[node]['node']
        if n.balance >= 1:
            if n.balance >= 20:
                return '#16b200'
            if n.balance >= 15:
                return '#31d619'
            if n.balance >= 10:
                return '#60ed4b'
            if n.balance >= 5:
                return '#87f776'
            return '#beffb5'
        if n.balance <= -1:
            if n.balance <= -20:
                return '#b20808'
            if n.balance <= -15:
                return '#ce2d2d'
            if n.balance <= -10:
                return '#e05c5c'
            if n.balance <= -5:
                return '#f28a8a'
            return '#ffb4b4'
        return '#cecece'

    def sendMessage(self, start, end, size, content):
        #print("\nSENDING MESSAGE FROM ", start, " TO ", end)

        self.stats.startRun()
        #print("\nUsing algorithm type: ", self.algorithm.name)
        startNode = self.graph.nodes[start]['node']
        message = startNode.createMessage(end, size, content)

        # Get path
        path = self.algorithm.getPath(self.graph, message, self.stats)
        self.stats.endRun(len(path))
        #print(path)

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
               # print("Decreasing from " + str(format(actualNode.costPerMByte, '.2f')) +
                      #" to " + str(format(actualNode.costPerMByte - DECREASE_AMOUNT, '.2f')))
                actualNode.decreasePrice()
            elif transmissionRate > INCREASE_THRESHOLD:
                #print("Increasing from " + str(format(actualNode.costPerMByte, '.2f')) +
                      #" to " + str(format(actualNode.costPerMByte + INCREASE_AMOUNT, '.2f')))
                actualNode.increasePrice()

        # Remove yourself from the path
        remainingPath.pop()

        # If you are the receiver, report. Else, continue transmitting.
        if currNode != message.endingNode:
            # print("Node ", currNode, " received message: ", message.content)
            # else
            return self.transmitMessageAndPayment(message, remainingPath)

    def runNetwork(self):
        a = datetime.datetime.now()
        self.sendMessage('D', 'M', 1, "Hello!")
        self.sendMessage('M', 'T', 2, "Hello 2!")
        self.sendMessage('A', 'C', 1, "Hello!")
        self.sendMessage('C', 'K', 1, "Hello!")
        self.sendMessage('L', 'M', 1, "Hello!")
        self.sendMessage('O', 'M', 1, "Hello!")
        self.sendMessage('D', 'T', 1, "Hello!")
        self.sendMessage('T', 'A', 1, "Hello!")
        self.sendMessage('B', 'R', 1, "Hello!")
        self.sendMessage('E', 'M', 1, "Hello!")
        self.sendMessage('C', 'L', 1, "Hello!")
        self.sendMessage('D', 'K', 1, "Hello!")
        self.sendMessage('B', 'O', 1, "Hello!")
        self.sendMessage('D', 'I', 1, "Hello!")
        self.sendMessage('A', 'T', 1, "Hello!")
        self.sendMessage('A', 'T', 1, "Hello!")
        self.sendMessage('A', 'T', 1, "Hello!")
        self.sendMessage('A', 'T', 1, "Hello!")
        self.sendMessage('A', 'T', 1, "Hello!")
        self.sendMessage('A', 'T', 1, "Hello!")
        self.sendMessage('A', 'T', 1, "Hello!")
        self.sendMessage('A', 'T', 1, "Hello!")
        self.sendMessage('A', 'T', 1, "Hello!")
        self.sendMessage('A', 'T', 1, "Hello!")
        self.sendMessage('A', 'T', 1, "Hello!")
        self.sendMessage('A', 'T', 1, "Hello!")
        self.sendMessage('A', 'T', 1, "Hello!")
        b=datetime.datetime.now()
        delta = b-a
        self.stats.recordTime(delta)
        cost = 0
        for node in self.graph.nodes():
            n = self.graph.node[node]['node']
            cost += n.costPerMByte
        cost /= float(len(self.graph.nodes))
        self.stats.recordCost(cost)

class StatsCollector():
    def __init__(self):
        #add run time for algorithm
        self.totalRuns = 0
        # Nodes queried per node chosen
        self.aggregate_NQPNC = 0
        self.current_run_nodes_queried = 0
        self.aggregate_path_length = 0
        self.timeToRun = 0
        self.averageCostPerMByte = 0


    def startRun(self):
        self.current_run_nodes_queried = 0

    def visitedNode(self):
        self.current_run_nodes_queried += 1

    def endRun(self, path_length):
        self.aggregate_path_length += path_length
        self.totalRuns += 1
        self.aggregate_NQPNC += self.current_run_nodes_queried/float(path_length)

    def recordTime(self, timeDif):
        self.timeToRun = timeDif.total_seconds()

    def recordCost(self, cost):
        self.averageCostPerMByte = cost;

    def printResults(self):
        print("The results of this test are:")
        print("The average number of nodes queried per node chosen are " + str(self.aggregate_NQPNC/float(self.totalRuns)))
        print("The average path length to send a message using this algorithm is " +
              str(self.aggregate_path_length/float(self.totalRuns)))
        print("The time it took to run this test was " + str(self.timeToRun) + " seconds")
        print("The average cost per MByte per node at the end was " + str(self.averageCostPerMByte))
        print('\n')


algorithms = [PathFindingAlgorithm.AStarAlgorithm('A*'),
              PathFindingAlgorithm.AgentApproach('Agent'),
              PathFindingAlgorithm.AgentApproximation('Approximation')]

for a in algorithms:
    statsCollector = StatsCollector()
    network = Network(a, statsCollector)
    network.runNetwork()
    statsCollector.printResults()

    for nodeName in network.graph.nodes:
        node = network.graph.nodes[nodeName]['node']
        print(node.name + ": " + format(node.balance, '.2f'))
    print('\n\n')

    network.draw()
