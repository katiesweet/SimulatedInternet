import networkx as nx
import matplotlib.pyplot as pyplot
import csv
import math
import copy


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
        self.nodes = {}

        with open('Intrinsic.csv') as nodeFile:
            nodes = csv.reader(nodeFile)
            for n in nodes:
                node = Node(n)
                self.nodes[node.name] = node
                self.graph.add_node(node.name, node=node, pos=(node.long, node.lat))

        with open('connections.csv') as connectionsFile:
            connections = csv.reader(connectionsFile)
            for c in connections:
                self.graph.add_edge(c[0], c[1], dist=self.euclideanDistance(c[0], c[1]))

    def draw(self):
        pos = nx.get_node_attributes(self.graph, 'pos')
        nx.draw(self.graph, pos, with_labels=True)
        pyplot.show()


    def euclideanDistance(self, node1, node2):
        latDist = abs(self.nodes[node1].lat - self.nodes[node2].lat)
        lonDist = abs(self.nodes[node1].long - self.nodes[node2].long)
        return math.sqrt(math.pow(latDist, 2) + math.pow(lonDist, 2))


    # TODO: Make this more interesting
    # def utilityFunction(self, message, node1, node2):
    def utilityFunction(self, message, node):
        speedPref = message.speedPref
        costPref = message.costPref
        size = message.size

        return speedPref * self.nodes[node].speed + costPref * self.nodes[node].costPerMByte * size


    # More of an agent based approach to the shortest path
    def getBid(self, current, message, visitedNodes):
        bestNeighbor = {'path': [], 'utility': float('inf'), 'totalCost': float('inf')}

        # Visit current node, and generate current nodes cost and utility
        currentVisitedNodes = copy.deepcopy(visitedNodes)
        currentVisitedNodes.append(current)

        myCost = self.nodes[current].costPerMByte * message.size
        myUtility = self.utilityFunction(message, current)

        # Get bids from other neighbors, and append yours on
        notVisitedNeighbors = list(set(self.graph.neighbors(current)) - set(visitedNodes))
        for neighbor in notVisitedNeighbors:

            # If neighbor is the destination
            if neighbor == message.endingNode:
                path = [(message.endingNode, 0)] # Ending node is final destination, and they charge nothing
                path.append((current, myCost))
                return { 'path' : path, 'utility' : myUtility, 'totalCost' : myCost}
            
            # Else
            neighborsOffer = self.getBid(neighbor, message, currentVisitedNodes)
            if neighborsOffer['utility'] < bestNeighbor['utility']:
                bestNeighbor = neighborsOffer

        # Now that we have our neighbors best offer, we can add ourself to it
        myOffer = {'path' : bestNeighbor['path'] + [(current, myCost)],
                   'utility' : bestNeighbor['utility'] + myUtility,
                   'totalCost' : bestNeighbor['totalCost'] + myCost}
        return myOffer

    # Based on the pseudocode given at : https://en.wikipedia.org/wiki/A*_search_algorithm
    # Requires some central understanding
    def aStarAlgorithm(self, message):
        # Set of nodes already evaluation
        closedSet = []        

        # Set of currently discovered nodes that are not evaluated yet
        # Initally only the start node is known
        openSet = [message.startingNode]

        # For each node, which node it can most efficiently be reached from.
        # If a node can be reached from many nodes, cameFrom will eventually contain the
        # most efficient previous step.
        cameFrom = {}

        # For each node, the cost of getting from the start node to that node
        gScores = {key: float('inf') for key in self.nodes}

        # The cost of going from start to start is zero
        gScores[message.startingNode] = 0

        # For each node, the total cost of getting from the start node ot the goal
        # by passing by that node. The value is partly known, partly heuristic
        fScores = {key: float('inf') for key in self.nodes}

        # For the first node, the value is completely heuristic
        fScores[message.startingNode] = self.euclideanDistance(message.startingNode, message.endingNode)

        while len(openSet) > 0:
            currFScores = {node: fScores[node] for node in openSet}
            current = min(currFScores, key=currFScores.get)

            if current == message.endingNode:
                return self.reconstructPath(cameFrom, current, gScores)
            
            openSet.remove(current)
            closedSet.append(current)

            for neighbor in self.graph.neighbors(current):
                if neighbor in closedSet:
                    continue # Ignore the neighbor which is already evaluated

                if neighbor not in openSet:
                    openSet.append(neighbor)
                
                # The distance from start to a neighbor
                # For our application, this is the utility function
                tentative_gScore = gScores[current] + self.utilityFunction(message, neighbor)

                if tentative_gScore >= gScores[neighbor]:
                    continue # This is not a better path

                # This is the current best path
                cameFrom[neighbor] = current
                gScores[neighbor] = tentative_gScore
                fScores[neighbor] = gScores[neighbor] + self.euclideanDistance(neighbor, message.endingNode)

        return False # Signal for failure for now

    def reconstructPath(self, cameFrom, current, gScores):
        """ Used in the A* algorithm to reconstruct the path """
        # NOTE: 
        # - returns totalPath = [('node', changeInUtility), ('node', changeInUtility), ...]
        # - the first node in totalPath is the destination, last node is the source
        # - Currently, the receiving node is also charging for the transmission
        # - The last node in the list (sending node) changeInBalance should be equal
        #   to the -1 * the sum of all other nodes changeInBalance
        #   (i.e. the last node pays, transmission nodes gain)

        totalCost = gScores[current]
        totalPath = []
        while current in cameFrom:
            nextInPath = cameFrom[current]
            currentsTake = gScores[current] - gScores[nextInPath]
            totalPath.append((current, currentsTake))
            current = nextInPath

        totalPath.append((current, -1*totalCost))
        return totalPath

    def getPath(self, message):
        bestBid = {'path': [], 'utility': float('inf'), 'totalCost': float('inf')}
        for neighbor in self.graph.neighbors(message.startingNode):
            bid = self.getBid(neighbor, message, [message.startingNode])
            if bid['utility'] < bestBid['utility']:
                bestBid = bid

        bestPath = bestBid['path'] + [(message.startingNode, -1*bestBid['totalCost'])]
        return bestPath

    def sendMessageAgentWise(self, start, end, size, content):
        print "\nSENDING MESSAGE AGENT WISE FROM ", start, " TO ", end
        message = Message(start,
                          end,
                          self.nodes[start].speedPref,
                          self.nodes[start].costPref,
                          size,
                          content)
        path = self.getPath(message)
        print path

        if path:
            self.transmitMessageAndPayment(message, path)


    def sendMessage(self, start, end, size, content):
        print "\nSENDING MESSAGE FROM ", start, " TO ", end
        message = Message(start,
                          end,
                          self.nodes[start].speedPref,
                          self.nodes[start].costPref,
                          size,
                          content)

        # Get path
        path = self.aStarAlgorithm(message)
        print path

        if path:
            self.transmitMessageAndPayment(message, path)

    def transmitMessageAndPayment(self, message, remainingPath):
        if len(remainingPath) <= 0:
            print "ERROR!"

        # Handle your own payment
        currNode, currPayment = remainingPath[-1]
        self.nodes[currNode].balance += currPayment
        print "Node ", currNode, " has a current balance of: ", self.nodes[currNode].balance

        # Remove yourself from the path
        remainingPath.pop()

        # If you are the receiver, report. Else, continue transmitting.
        if currNode == message.endingNode:
            print "Node ", currNode, " received message: ", message.content
        else:
            return self.transmitMessageAndPayment(message, remainingPath)

network = Network()

network.sendMessage('D', 'M', 1, "Hello!")
network.sendMessageAgentWise('D', 'M', 1, 'Agent Hello!')
network.sendMessage('M', 'T', 2, "Hello 2!")
network.sendMessageAgentWise('M', 'T', 2, 'Agent Hello 2!')

network.draw()
