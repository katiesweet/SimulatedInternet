from abc import ABCMeta, abstractmethod
import networkx as nx
import math
import copy


class PathFindingAlgorithm:
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def getPath(self, graph, message):
        raise NotImplementedError()

    def euclideanDistance(self, graph, node1, node2):
        firstNode = self.getNode(graph, node1)
        secondNode = self.getNode(graph, node2)
        latDist = abs(firstNode.lat - secondNode.lat)
        lonDist = abs(firstNode.long - secondNode.long)
        return math.sqrt(math.pow(latDist, 2) + math.pow(lonDist, 2))

    # TODO: Make this more interesting
    # def utilityFunction(self, message, node1, node2):
    def utilityFunction(self, message, node):

        speedPref = message.speedPref
        costPref = message.costPref
        size = message.size

        return speedPref * node.speed * size + costPref * node.costPerMByte * size

    def getNode(self, graph, nodeName):
        return graph.nodes[nodeName]['node']


class AStarAlgorithm(PathFindingAlgorithm):
    # Based on the pseudocode given at : https://en.wikipedia.org/wiki/A*_search_algorithm
    # Requires some central understanding
    def getPath(self, graph, message):
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
        gScores = {key: float('inf') for key in nx.nodes(graph)}

        # The cost of going from start to start is zero
        gScores[message.startingNode] = 0

        # For each node, the total cost of getting from the start node ot the goal
        # by passing by that node. The value is partly known, partly heuristic
        fScores = {key: float('inf') for key in nx.nodes(graph)}

        # For the first node, the value is completely heuristic
        fScores[message.startingNode] = self.euclideanDistance(
            graph, message.startingNode, message.endingNode)

        while len(openSet) > 0:
            currFScores = {node: fScores[node] for node in openSet}
            current = min(currFScores, key=currFScores.get)

            if current == message.endingNode:
                return self.reconstructPath(cameFrom, current, graph, message)

            openSet.remove(current)
            closedSet.append(current)

            for neighbor in nx.all_neighbors(graph, current):
                if neighbor in closedSet:
                    continue  # Ignore the neighbor which is already evaluated

                if neighbor not in openSet:
                    openSet.append(neighbor)

                # The distance from start to a neighbor
                # For our application, this is the utility function
                neighborNode = graph.node[neighbor]['node']
                tentative_gScore = gScores[current] + \
                    self.utilityFunction(message, neighborNode)

                if tentative_gScore >= gScores[neighbor]:
                    continue  # This is not a better path

                # This is the current best path
                cameFrom[neighbor] = current
                gScores[neighbor] = tentative_gScore
                fScores[neighbor] = gScores[neighbor] + \
                    self.euclideanDistance(graph, neighbor, message.endingNode)

        return False  # Signal for failure for now

    def reconstructPath(self, cameFrom, current, graph, message):
        """ Used in the A* algorithm to reconstruct the path """
        # NOTE:
        # - returns totalPath = [('node', changeInUtility), ('node', changeInUtility), ...]
        # - the first node in totalPath is the destination, last node is the source
        # - Currently, the receiving node is also charging for the transmission
        # - The last node in the list (sending node) changeInBalance should be equal
        #   to the -1 * the sum of all other nodes changeInBalance
        #   (i.e. the last node pays, transmission nodes gain)

        totalCost = 0
        totalPath = []
        while current in cameFrom:
            nextInPath = cameFrom[current]
            currentsTake = self.getChargedCost(graph, message, current)
            totalCost += currentsTake
            totalPath.append((current, currentsTake))
            current = nextInPath

        totalPath.append((current, -1*totalCost))
        return totalPath

    def getChargedCost(self, graph, message, current):
        node = self.getNode(graph, current)
        return node.costPerMByte * message.size


class AgentApproach(PathFindingAlgorithm):
    def getPath(self, graph, message):
        bestBid = {'path': [], 'utility': float(
            'inf'), 'totalCost': float('inf')}
        for neighbor in graph.neighbors(message.startingNode):
            bid = self.getBid(graph, neighbor, message, [message.startingNode])
            if bid['utility'] < bestBid['utility']:
                bestBid = bid

        bestPath = bestBid['path'] + \
            [(message.startingNode, -1*bestBid['totalCost'])]
        return bestPath

    def getBid(self, graph, current, message, visitedNodes):
        myNode = graph.nodes[current]['node']
        myCost = myNode.costPerMByte * message.size
        myUtility = self.utilityFunction(message, myNode)

        # If current is message recipient, we are done
        if current == message.endingNode:
            return {'path': [(message.endingNode, myCost)],
                    'utility': myUtility,
                    'totalCost': myCost}

        # Visit current node, and generate current nodes cost and utility
        currentVisitedNodes = copy.deepcopy(visitedNodes)
        currentVisitedNodes.append(current)

        # Get neighbors best bid
        bestNeighbor = {'path': [], 'utility': float(
            'inf'), 'totalCost': float('inf')}
        notVisitedNeighbors = list(
            set(graph.neighbors(current)) - set(currentVisitedNodes))
        for neighbor in notVisitedNeighbors:
            messageSender = message.messageId[0]
            messageId = message.messageId[1]
            neighborNode = self.getNode(graph, neighbor)
            if messageSender not in neighborNode.messagesSeen or messageId != neighborNode.messagesSeen[messageSender]:
                neighborNode.messagesSeen[messageSender] = messageId
                neighborNode.numMessagesSeen += 1

            neighborsOffer = self.getBid(
                graph, neighbor, message, currentVisitedNodes)
            if neighborsOffer['utility'] < bestNeighbor['utility']:
                bestNeighbor = neighborsOffer

        # Now that we have our neighbors best offer, we can add ourself to it
        myOffer = {'path': bestNeighbor['path'] + [(current, myCost)],
                   'utility': bestNeighbor['utility'] + myUtility,
                   'totalCost': bestNeighbor['totalCost'] + myCost}
        return myOffer
