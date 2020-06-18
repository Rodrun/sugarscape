from event import Event
from config import GESTATION_MU, GESTATION_SIGMA, REPRODUCTION_LAMBDA, FERTILE_AGE,\
    MEAN_MAX_AGE, SIGMA_MAX_AGE
import math
import plotly.express as px
from rng import RNG


class Agent:
    def __init__(self, landscape, calendar, rng, aList, id=None, t=0, row=None, col=None, metab=None,
        vision=None, mother=None, max_age=None, initial_sugar=0):
        """
        calendar - EventCalendar.
        rng - RNG. 
        aList - Host AgentList.
        id - Identifier.
        t - Time of birth.
        row - Spawn row.
        col - Spawn column.
        metab - Metabolic rate per time step, if None random value is assigned.
        vision - Visio
         distance, if None random value is assigned.
        mother - Is mother? (Can reproduce & birth child?)
        max_age - Maximum age.
        initial_sugar - Initial sugar alotted (Agent still eats at Cell it is spawned in).
        """
        self.id = id
        self.rng = rng
        self.sugar = initial_sugar
        self.t_lastNextSugar = t # Time when update_sugar() was last called
        self.mate = None # Who to combine genetics with
        self.alive = True
        self.birthdate = t # Time of birth, of course

        self.landscape = landscape
        self.calendar = calendar
        self.agentList = aList

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
        self.max_age = max_age if max_age != None else abs(rng.get("genetic").normal(MEAN_MAX_AGE, SIGMA_MAX_AGE))

        # Time keep
        self.t_nextEventTime, self.t_nextEventType, self.nextCallback = math.inf, None, None
        self.t_move = t + rng.get("inter").exponential(1.0) # When to move
        self.move_event = None
        self.t_die  = math.inf # When to die
        self.die_event = None
        if self.mother:
            self.t_reproduce = t + FERTILE_AGE + rng.get("inter").exponential(REPRODUCTION_LAMBDA)
        else:
            self.t_reproduce = math.inf
        self.reproduce_event = None
        self.t_birth = math.inf # When to give birth
        self.birth_event = None
        self.period_g = math.inf # Gestation period length

        self.eat(landscape.get_cell(self.col, self.row)) # Eat initial sugar
        self.check_for_death()
        if self.t_die != t: # Survives birth?
            self.move_event = self._sched(Event(self.t_move, Event.MOVE, self, self.move))
            self.reproduce_event = self._sched(Event(self.t_reproduce, Event.REPRODUCE, self, self.reproduce))

    def _sched(self, event):
        """Schedule an event. This also conveniently calls check_for_death().
        Returns scheduled event (value returned by EventList.add()). None if event time is inf.
        """
        #print(f"_sched{event.time, event.type} by Agent {self.id}")
        self.check_for_death()
        if event.time != math.inf:
            return self.calendar.add(event)
        return None

    def die(self):
        print(f"Agent {self.id} is now DEAD!!!!!!!!!! RIP at {self.calendar.now()} w/ {self.sugar} sugar max_age = {self.max_age}")
        self.alive = False
        self.t_nextEventTime = math.inf
        self.t_nextEventType = None
        self.nextCallback = None
        self.landscape.remove(self.col, self.row)
        self.agentList.remove(self)
        # Hard-coded cancellation of scheduled events past death
        self.calendar.cancels(
            self.reproduce_event,
            self.move_event,
            self.birth_event
        )

    def eat(self, cell):
        """Eat the sugar at current location."""
        self.sugar += cell.sugar
        cell.sugar = 0

    def field_of_view(self, evaluate):
        """Iterate through the field of view.
        evaluate - Callable with current Cell parameter and distance from Agent parameter.
        """
        landscape = self.landscape # TODO: refactor

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

    def moore_neighborhood(self, evaluate):
        """Iterate through the Moore neighborhood.
        evaluate - Callable with current Cell parameter.
        """
        landscape = self.landscape # TODO: refactor

        if not callable(evaluate):
            raise TypeError("moore_neighborhood() requires a callable evaluate parameter")
        yRange = [0, 1, 2]
        xRange = [0, 1, 2]
        self.rng.get("shuffle").shuffle(yRange)
        self.rng.get("shuffle").shuffle(xRange)
        for y in yRange:
            checkY = self.row - 1 + y
            for x in xRange:
                checkX = self.col - 1 + x
                checkCell = landscape.get_cell(checkX, checkY)
                if checkCell.agent != self:
                    evaluate(checkCell)

    def reproduce(self):
        """Look for another Agent in the FOV to reproduce with.
        Only Agents with mother = True choose their mate. Smash the patriarchy.
        Modified reproduce rule:
            - Find wealthiest non-mother Agent within the FOV.
            - If Agent cannot find a candidate, reschedule reproduction event.
            - If viable candidate chosen, schedule birth event.
        """
        self.update_sugar()
        calendar = self.calendar # TODO: refactor so this block isn't necessary
        landscape = self.landscape
        t = calendar.now()

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
            self.field_of_view(find_wealthiest)

            if wealthiest:
                self.mate = wealthiest
                self.period_g = abs(self.rng.get("inter").normal(GESTATION_MU, GESTATION_SIGMA))
                self.t_birth = t + self.period_g
                self.t_reproduce = math.inf
            else:
                self.t_reproduce = t + self.rng.get("inter").exponential(REPRODUCTION_LAMBDA)
        else:
            self.t_reproduce = t + self.rng.get("inter").exponential(REPRODUCTION_LAMBDA)

        if self.mate != None:
            self.birth_event = self._sched(Event(self.t_birth, Event.BIRTH, self, self.birth))
        else:
            self.reproduce_event = self._sched(Event(self.t_reproduce, Event.REPRODUCE, self, self.reproduce))

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
        self.moore_neighborhood(evaluate)
        return maxCell

    def birth(self):
        """Give birth, if an empty neighboring Cell is available. Only mother Agents give birth.
        Modified birth rule:
            - Look for an emtpy cell in the Moore neighborhood with the most sugar.
            - If an empty cell cannot be found in the Moore neighborhood, cancel birth.
            - Offspring will have metabolism and vision traits randomly inherited from parents.
        """
        self.update_sugar()
        calendar = self.calendar # TODO: refactor so this block isn't necessary
        t = calendar.now()
        landscape = self.landscape

        baby = None
        #if self.alive:
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
                aList=self.agentList,
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
            self.agentList.full_add(baby)

            self.mate = None
            self.t_birth = math.inf
            # Schedule next reproduction event
            self.t_reproduce = t + self.rng.get("inter").exponential(REPRODUCTION_LAMBDA)
            self.reproduce_event = self._sched(Event(self.t_reproduce, Event.REPRODUCE, self, self.reproduce))

    def is_gestating(self, t):
        """Agent is gestating at time t?"""
        if self.period_g == math.inf:
            return False
        return t <= self.t_reproduce + self.period_g

    def move(self):
        """Move agent to best possible nearby spot."""
        self.update_sugar()
        calendar = self.calendar # TODO: refactor so this block isn't necessary
        t = calendar.now()
        landscape = self.landscape

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

        self.field_of_view(evaluate)

        if maxCell:
            # Move, then eat
            landscape.move(self.col, self.row, maxCell.x, maxCell.y)
            self.eat(maxCell)
        # Schedule next move
        self.t_move = t + abs(self.rng.get("inter").exponential(1.0))
        self.move_event = self._sched(Event(self.t_move, Event.MOVE, self, self.move))

    def _compute_sugar(self, ti, tf, si):
        """Compute sugar. sf = -metab(tf - ti) + si.
        ti - Initial time.
        tf - Final time.
        si - Initial sugar.
        """
        return (-self.metab * (tf - ti)) + si

    def update_sugar(self):
        """Update the current sugar level."""
        #print(f"Agent {self.id} update_sugar() executed at t = {self.calendar.now()}")
        #print(f"Agent {self.id} {self.sugar} -= {self.metab} * ({self.calendar.now()} - {self.t_lastNextSugar})")
        #self.sugar = -self.metab * (self.t_lastNextSugar - self.calendar.now()) + self.sugar
        self.sugar = self._compute_sugar(self.t_lastNextSugar, self.calendar.now(), self.sugar)
        #print(f"Agent {self.id} sugar = {self.sugar}")
        self.t_lastNextSugar = self.calendar.now()
        #assert self.sugar > 0

    def _compute_death(self):
        # Compute time of death, this is to replace the old function
        # First, calculate time of death (y = mx + b, calculate when y = 0)
        # Note that we already know b = sugar, m = metab, y = 0, x = ?
        # Thus our equation will be -b/m = x
        death = self.calendar.now() + (-self.sugar / -self.metab)
        #print(f"({self.id}) Calc'd death for {death}. sf = {(-self.metab * (death - self.calendar.now())) + self.sugar}")
        #assert 0 >= (-self.metab * (death - self.calendar.now())) + self.sugar
        #print(f"death = {self.calendar.now()} + (-{self.sugar} / -{self.metab})")
        # Second, compare if calculated death or max age is first, return the minimum of both
        old_age = self.birthdate + self.max_age
        #print(f"death = {death}, old_age = {old_age} calc'd by Agent {self.id}")
        self.t_die = min([death, old_age])

    def check_for_death(self):
        """Check for death and appropriately schedule death time."""
        self._compute_death()
        if self.sugar <= 0:
            self.t_die = self.calendar.now() # This is not good, TODO fix the negative sugar bug!
        #print(f"Computed deathTime = {self.t_die} calc'd at t = {self.calendar.now()}")
        if self.die_event != None:
            self.die_event = self.calendar.resched(self.die_event, self.t_die)
        else:
            self.die_event = self.calendar.add(Event(self.t_die, Event.DIE, self, self.die))


class AgentList:
    """Store agents and compute statistics."""
    SUGAR = lambda agent: agent.sugar
    METABOLISM = lambda agent: agent.metab
    VISION = lambda agent: agent.vision

    def __init__(self, initialAmt, landscape, calendar, rng):
        self.current_id = 0
        self.agentList = []
        for i in range(initialAmt):
            newAgent = Agent(landscape, calendar, aList=self, rng=rng)
            self.full_add(newAgent)

    def add(self, agent):
        """Add agent to Agent list."""
        if isinstance(agent, Agent):
            agent.id = self.current_id
            self.agentList.append(agent)
            self.current_id += 1
        else:
            raise TypeError("add() requires Agent as parameter")

    def full_add(self, agent):
        self.add(agent)
        landscape = agent.landscape
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

    def remove(self, agent):
        try:
            self.agentList.remove(agent)
        except:
            print(f"WARNING: Tried to remove agent {agent.id} who is not in the Agent list")

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
