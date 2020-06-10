from event import Event
from config import GESTATION_MU, GESTATION_SIGMA, REPRODUCTION_LAMBDA, FERTILE_AGE,\
    MEAN_MAX_AGE, SIGMA_MAX_AGE
import math
import plotly.express as px
from rng import RNG


class Agent:
    def __init__(self, landscape, calendar, rng, id=None, t=0, row=None, col=None, metab=None,
        vision=None, mother=None, max_age=None, initial_sugar=0):
        """
        landscape - Target Landscape.
        calendar - EventCalendar.
        id - Identifier.
        t - Time of birth.
        row - Landscape row, if None will randomly choose both row and col.
        col - Landscape column, if None will randomly choose both row and col.
        metab - Metabolic rate per time step, if None random value is assigned.
        vision - Vision distance, if None random value is assigned.
        mother - Is mother? (Can reproduce & birth child?)
        max_age - Maximum age.
        initial_sugar - Initial sugar alotted (Agent still eats at Cell it is spawned in).
        """
        self.id = id
        self.rng = rng
        self.sugar = initial_sugar
        self.nextSugar = 0 # Calculated sugar by the time of next move event
        self.mate = None # Who to combine genetics with
        self.alive = True
        self.birthdate = t # Time of birth, of course

        self.row = row
        self.col = col
        if row == None or col == None:
            self.col, self.row = landscape.next_open()
        if self.row == None or self.row == None:
            raise Exception("No more open spots on landscape!")

        # Genetic traits
        self.metab = metab if metab != None else rng.get("genetic").uniform(1, 4)
        self.vision = vision if vision != None else math.ceil(rng.get("genetic").uniform(1, 6))
        self.mother = mother if mother != None else rng.get("genetic").choice([True, False])
        self.max_age = max_age if max_age != None else rng.get("genetic").normal(MEAN_MAX_AGE, SIGMA_MAX_AGE)

        # Time keep
        self.t_nextEventTime, self.t_nextEventType = math.inf, None
        self.t_move = t + rng.get("inter").exponential(1.0) # When to move
        self.t_die  = math.inf # When to die
        if self.mother:
            self.t_reproduce = t + FERTILE_AGE + rng.get("inter").exponential(REPRODUCTION_LAMBDA)
        else:
            self.t_reproduce = math.inf
        self.t_birth = math.inf # When to give birth
        self.period_g = math.inf # Gestation period length

        self.eat(landscape.get_cell(self.col, self.row)) # Eat initial sugar
        self.setNextEvent(t, calendar)

    def _minimum_pair(self, values, results):
        """Given a list of values with corresponding list of results, return the pair with the minimum value.
        For example, _minimum_pair([5, 100], ["a", "b"]) -> (5, "a").
        Does not take into account if all values are math.inf (TODO).
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

    def _maximum_pair(self, values, results):
        """Given a list of values with corresponding list of results, return the pair with the maximum value.
        For example, _minimum_pair([5, 100], ["a", "b"]) -> (100, "b").
        If all values are -inf, will return (-inf, result[0]).
        """
        assert len(values) == len(results)
        maxIndex = math.inf
        maxValue = -math.inf
        for i in range(len(values)):
            val = values[i]
            if val > maxValue:
                maxValue = val
                maxIndex = i
        if maxIndex == math.inf:
            result = results[0]
        else:
            result = results[maxIndex]
        return maxValue, result

    def get_next_event(self):
        """Get the next event time and event type."""
        return self._minimum_pair(
            [self.t_move, self.t_die, self.t_reproduce, self.t_birth],
            [Event.MOVE, Event.DIE, Event.REPRODUCE, Event.BIRTH]
        )

    def setNextEvent(self, t, calendar):
        self.t_nextEventTime, self.t_nextEventType = self.get_next_event()
        self.check_for_death(t, self.t_nextEventTime)
        self.t_nextEventTime, self.t_nextEventType = self.get_next_event()
        calendar.add(Event(self.t_nextEventTime, self.t_nextEventType, self))
        # Compute Agent's sugar amount by time of next event
        self.nextSugar = self.compute_sugar(t, self.t_nextEventTime)

    def eat(self, cell):
        """Eat the sugar at current location."""
        self.sugar += cell.sugar
        cell.sugar = 0

    def field_of_view(self, landscape, evaluate):
        """Iterate through the field of view.
        landscape - Agent's Landscape.
        evaluate - Callable with current Cell parameter and distance from Agent parameter.
        """
        if not callable(evaluate):
            raise TypeError("field_of_view() requires a callable evaluate parameter")
        agentCell = landscape.get_cell(self.col, self.row)
        directions = [[0, 1], [1, 0], [0, -1], [-1, 0]]
        self.rng.get("shuffle").shuffle(directions)
        for direction in directions:
            for dist in range(self.vision):
                x = self.col + direction[0]
                y = self.row + direction[1]
                currentCell = landscape.get_cell(x, y)
                # Cells that are too high are not part of the FOV
                if currentCell.level <= self.vision + agentCell.level:
                    evaluate(currentCell, dist)

    def moore_neighborhood(self, landscape, evaluate):
        """Iterate through the Moore neighborhood.
        landscape - Agent's Landscape.
        evaluate - Callable with current Cell parameter.
        """
        if not callable(evaluate):
            raise TypeError("moore_neighborhood() requires a callable evaluate parameter")
        for y in range(3):
            checkY = self.row - 1 + y
            for x in range(3):
                checkX = self.col - 1 + x
                checkCell = landscape.get_cell(checkX, checkY)
                if checkCell.agent != self:
                    evaluate(checkCell)

    def reproduce(self, t, landscape, calendar):
        """Look for another Agent in the FOV to reproduce with.
        Only Agents with mother = True choose their mate. Smash the patriarchy.
        Modified reproduce rule:
            - Find wealthiest non-mother Agent within the FOV.
            - If Agent cannot find a candidate, reschedule reproduction event.
            - If viable candidate chosen, schedule birth event.
        """
        self.sugar = self.nextSugar
        if self.mother:
            # Find wealthiest non-mother Agent
            wealthiest = None
            maxSugar = -math.inf
            def find_wealthiest(cell, dist):
                nonlocal wealthiest
                nonlocal maxSugar
                if cell.agent != None:
                    cand = cell.agent
                    if cell.sugar > maxSugar and not cand.is_gestating(t) and cand.alive:
                        wealthiest = cand
                        maxSugar = cell.sugar
            self.field_of_view(landscape, find_wealthiest)

            if wealthiest:
                self.mate = wealthiest
                self.period_g = self.rng.get("inter").normal(GESTATION_MU, GESTATION_SIGMA)
                self.t_birth = t + self.period_g
                self.t_reproduce = math.inf
            else:
                self.t_reproduce = t + self.rng.get("inter").exponential(REPRODUCTION_LAMBDA)
        else:
            self.t_reproduce = t + self.rng.get("inter").exponential(REPRODUCTION_LAMBDA)
        self.setNextEvent(t, calendar)

    def get_best_birth_cell(self, landscape):
        """Get an empty Cell with the most sugar in the Moore neighborhood, if there is one."""
        maxCell, maxSugar = None, -math.inf
        def evaluate(cell):
            nonlocal maxCell
            nonlocal maxSugar
            if cell.agent == None:
                if cell.sugar > maxSugar:
                    maxSugar = cell.sugar
                    maxCell = cell
        self.moore_neighborhood(landscape, evaluate)
        return maxCell

    def birth(self, t, landscape, calendar):
        """Give birth, if an empty neighboring Cell is available. Only mother Agents give birth.
        Modified birth rule:
            - Look for an emtpy cell in the Moore neighborhood with the most sugar.
            - If an empty cell cannot be found in the Moore neighborhood, cancel birth.
            - Offspring will have metabolism and vision traits randomly inherited from parents.
        Returns offspring Agent, None if birth failed.
        """
        self.sugar = self.nextSugar
        baby = None
        if self.alive:
            birthCell = self.get_best_birth_cell(landscape)
            if birthCell != None:
                # Randomly choose inherited traits
                # It's not necessarily Mendelian, but works for now
                metab = self.rng.get("genetic").choice([self.metab, self.mate.metab])
                vision = self.rng.get("genetic").choice([self.vision, self.mate.vision])
                max_age = self.rng.get("genetic").choice([self.max_age, self.mate.max_age])
                # Inheritance
                selfInherit = self.sugar / 2
                mateInherit = self.mate.sugar / 2
                # Give birth
                baby = Agent(landscape, calendar,
                    row=birthCell.y,
                    col=birthCell.x,
                    t=t,
                    rng=self.rng,
                    metab=metab,
                    vision=vision,
                    max_age=max_age,
                    initial_sugar=selfInherit + mateInherit)
                # Adjust for inheritance
                self.sugar -= selfInherit
                self.mate.sugar -= mateInherit

        self.mate = None
        self.t_birth = math.inf
        # Schedule next reproduction event
        self.t_reproduce = t + self.rng.get("inter").exponential(REPRODUCTION_LAMBDA)
        self.setNextEvent(t, calendar)
        return baby

    def is_gestating(self, t):
        """Agent is gestating at time t?"""
        if self.period_g == math.inf:
            return False
        return t <= self.t_reproduce + self.period_g

    def move(self, t, landscape, calendar):
        """Move agent to best possible nearby spot."""
        self.sugar = self.nextSugar # Calculate current amount of sugar after metabolism
        # Scan in the cardinal directions & search for max visible sugar
        # If multiple max sugar values found, go to nearest
        maxSugar, maxCell, minDist = -1, None, math.inf
        def evaluate(cell, dist):
            nonlocal maxSugar
            nonlocal maxCell
            nonlocal minDist
            if not cell.agent: # Empty?
                if cell.sugar > maxSugar:
                    maxSugar = cell.sugar
                    maxCell = cell
                    minDist = dist
                elif cell.sugar == maxSugar:
                    # Choose nearest when there are equal contenders
                    if dist < minDist:
                        maxCell = currentCell

        self.field_of_view(landscape, evaluate)

        if maxCell:
            # Move, then eat
            landscape.move(self.col, self.row, maxCell.x, maxCell.y)
            self.eat(maxCell)
        # Schedule next move
        self.t_move = t + abs(self.rng.get("inter").exponential(1.0))
        self.setNextEvent(t, calendar)

    def compute_sugar(self, tNow, tThen):
        """Compute sugar amount by tThen.
        Returns float sugar amount.
        """
        return self.sugar + (-self.metab * (tThen - tNow))

    def compute_death(self, tNow, tHopeful):
        """Compute time of death.
        tNow - Current time.
        tHopeful - Time of next event.
        Returns float time if death is expected, otherwise -inf.
        """
        expectedAmount = self.compute_sugar(tNow, tHopeful)
        if expectedAmount <= 0:
            m = (expectedAmount - self.sugar) / (tHopeful - tNow)
            return tNow + (-self.sugar / m)
        if tHopeful >= self.max_age:
            return self.birthdate + self.max_age
        return -math.inf

    def check_for_death(self, t, t_next):
        """Check for death and appropriately assign death time.
        t - Current time.
        t_next - Hopeful next scheduled event time.
        """
        deathTime = self.compute_death(t, t_next)
        if deathTime != -math.inf:
            if deathTime < self.t_move:
                self.t_die = deathTime


class AgentList:
    """Store agents and compute statistics."""
    SUGAR = lambda agent: agent.sugar
    METABOLISM = lambda agent: agent.metab
    VISION = lambda agent: agent.vision

    def __init__(self, initialAmt, landscape, calendar, rng):
        self.current_id = 0
        self.agentList = []
        for i in range(initialAmt):
            newAgent = Agent(landscape, calendar, rng=rng)
            self.full_add(newAgent, landscape)

    def add(self, agent):
        """Add agent to Agent list."""
        if isinstance(agent, Agent):
            agent.id = self.current_id
            self.agentList.append(agent)
            self.current_id += 1
        else:
            raise TypeError("add() requires Agent as parameter")

    def full_add(self, agent, landscape):
        """Add agent to Agent list and given Landscape."""
        self.add(agent)
        success = landscape.put(agent, agent.col, agent.row)
        if not success:
            occ = landscape.get_cell(agent.col, agent.row).agent.id
            raise Exception(f"Cannot put Agent {agent.id} at {agent.col, agent.row}, occupied by {occ}")

    def get_by_id(self, id):
        """Search for and return an Agent by id.
        Returns None if not found.
        """
        for agent in self.agentList:
            if agent.id == id:
                return agent
        return None

    def remove(self, agent, calendar, landscape):
        """Remove agent from the state (AgentList, EventCalendar, Landscape)."""
        try:
            self.agentList.remove(agent)
            landscape.remove(agent.col, agent.row)
            calendar.remove_agent(agent)
        except:
            print(f"WARNING: Tried to remove agent {agent.id}")

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
        Invalid stat option/too few population returns None. Empty population returns 0.
        """
        l = len(self.agentList)
        if l == 0:
            return 0
        ordered = self.ordered_by(stat)
        if ordered == None:
            return None
        lowMid = math.floor(l / 2)
        hiMid = math.ceil((l + 1) / 2)
        try:
            compMed = (stat(ordered[lowMid]) + stat(ordered[hiMid])) / 2
        except IndexError as inerr:
            return None
        return compMed
