from event import Event
import math
import plotly.express as px
import random


class Agent:
    def __init__(self, landscape, calendar, id=None):
        self.id = id
        self.sugar = 0 # Placeholder value
        self.nextSugar = 0 # Calculated sugar by the time of next move event
        
        self.row, self.col = landscape.next_open()
        if self.row == None or self.row == None:
            raise Error("No more open spots on landscape!")

        # Genetic traits
        self.metab = random.uniform(1, 4)
        self.vision = math.ceil(random.uniform(1, 6))

        # Time keep
        self.t_move = random.expovariate(1.0) #exp(1.0)
        self.t_die  = math.inf
        self.t_nextEventTime, self.t_nextEventType = math.inf, None
        #self.t_reproduce = lognormal(4, 2.5)

        self.eat(landscape.get_cell(self.col, self.row)) # Eat initial sugar
        self.setNextEvent(calendar)

    # Temporary(?) workaround
    def _minimum_pair(self, values, results):
        """Given a list of values with corresponding list of results, return the pair with the minimum value.
        For example, minimum_pair([5, 100], ["a", "b"]) -> (5, "a").
        """
        assert len(values) == len(results) # Every value needs a corresponding results element
        minIndex = math.inf
        minValue = math.inf
        for i in range(len(values)):
            val = values[i]
            if val < minValue:
                minValue = val
                minIndex = i
        return minValue, results[minIndex]

    def setNextEvent(self, calendar):
        self.t_nextEventTime, self.t_nextEventType = self._minimum_pair(
            [self.t_move, self.t_die],
            [Event.MOVE, Event.DIE]
        )
        calendar.calendar.append(Event(self.t_nextEventTime, self.t_nextEventType, self))

    def eat(self, cell):
        """Eat the sugar at current location."""
        self.sugar += cell.sugar
        cell.sugar = 0

    def move(self, t, landscape, calendar):
        """Move agent to best possible nearby spot."""
        self.sugar = self.nextSugar
        # algorithm for moving
        # Scan in the cardinal directions & search for max visible sugar
        # If multiple max sugar values found, go to nearest
        maxSugar, maxCell, minDist = -1, None, math.inf
        # Shuffle direction order
        directions = [[0, 1], [1, 0], [0, -1], [-1, 0]]
        random.shuffle(directions)
        for direction in directions:
            for dist in range(self.vision):
                x = self.col + direction[0]
                y = self.row + direction[1]
                currentCell = landscape.get_cell(x, y)
                if currentCell and currentCell.level <= self.vision + landscape.get_cell(self.col, self.row).level:
                    if landscape.is_empty(x, y): # Empty?
                        if currentCell.sugar > maxSugar:
                            maxSugar = currentCell.sugar
                            maxCell = currentCell
                            minDist = dist
                        elif currentCell.sugar == maxSugar:
                            # Choose nearest when there are equal contenders
                            if dist < minDist:
                                maxCell = currentCell
                else:
                    break # Go to next direction, if any

        if maxCell:
            # Move, then eat
            landscape.move(self.col, self.row, maxCell.x, maxCell.y)
            self.eat(maxCell)
        # schedule next move
        self.t_move = t + random.expovariate(1.0)
        #self.t_move = t + 1.0
    
        # Do we die before next scheduled move?
        # If so, schedule death at computed time.
        # For now, only compare to t_move, rather than next event.
        # Compute how much sugar will be metabolised by t_move. y = b + mt
        expectedAmount = self.sugar - self.metab * (self.t_move - t)
        # If expectedAmount is <= 0, schedule death
        if expectedAmount <= 0:
            # Compute time of death with basic algebra
            # 0 = b + mt
            # -b = mt
            # -b/m = t
            self.t_die = -self.sugar / self.metab
        else:
            self.nextSugar = expectedAmount

        self.setNextEvent(calendar)

    def die(self, landscape, alist):
        """Remove from landscape and agentlist."""
        landscape.remove(self.col, self.row)
        alist.remove(self)


class AgentList:
    """Store agents and compute statistics."""
    SUGAR = lambda agent: agent.sugar
    METABOLISM = lambda agent: agent.metab
    VISION = lambda agent: agent.vision

    def __init__(self, initialAmt, landscape, calendar):
        self.current_id = 0
        self.agentList = set()
        for i in range(initialAmt):
            newAgent = Agent(landscape, calendar, self.current_id)
            self.agentList.add(newAgent)
            landscape.put(newAgent, newAgent.col, newAgent.row)
            self.current_id += 1

    def remove(self, agent):
        if agent in self.agentList:
            self.agentList.remove(agent)

    def average(self, stat):
        """Get the average given stat of the agent population.
        Possible stat options:
        - SUGAR
        - METABOLISM
        - VISION
        Empty population will return 0.
        """
        if len(self.agentList) == 0:
            return 0
        aSum = 0
        for agent in self.agentList:
            aSum += stat(agent)
        return aSum / len(self.agentList)

    def ordered_by(self, stat, reversed=False):
        """Get an ascending order list by a given stat of all the agents.
        Returns descending order if reversed = True.
        Possible stat options:
        - SUGAR
        - METABOLISM
        - VISION
        """
        ordered = list(self.agentList)
        ordered.sort(key=stat, reverse=reversed)
        return ordered

    def median(self, stat):
        """Get the median stat of the agent population.
        Possible stat options:
        - SUGAR
        - METABOLISM
        - VISION
        Invalid stat option returns None. Empty population returns 0.
        """
        l = len(self.agentList)
        if l == 0:
            return 0
        ordered = self.ordered_by(stat)
        if ordered == None:
            return None
        lowMid = math.floor(l / 2)
        hiMid = math.ceil((l + 1) / 2)
        return (stat(ordered[lowMid]) + stat(ordered[hiMid])) / 2
