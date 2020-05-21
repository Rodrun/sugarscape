from agent import Agent
from config import MAX_HEIGHT, MAX_POSSIBLE_SUGAR, ALPHA
import random


class Cell:
    """The bones of the Landscape: every coordinate is an individual Cell."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.capacity = random.randint(0, MAX_POSSIBLE_SUGAR)
        self.sugar = self.capacity
        self.level = random.randint(1, MAX_HEIGHT) # Synonymous with height
        self.agent = None

    def update_sugar(self, tLast, tNow):
        """Update the sugar count. tLast is the last time the count was updated, tNow is current time."""
        diff = tNow - tLast
        self.sugar += diff * ALPHA
        if self.sugar > self.capacity: # Ensure sugar does not exceed given capacity
            self.sugar = self.capacity


class Landscape:
    """The world that hosts Cells that hold Agents and sugar."""
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.landscape = [[Cell(x, y) for x in range(self.cols)] for y in range(self.rows)]
        self.population = 0
        self.t_lastSugarUpdate = 0

    def valid_coord(self, x, y):
        """Return true if (x, y) are real coordinates the landscape."""
        satisfy_x = x >= 0 and x < self.cols
        satisfy_y = y >= 0 and y < self.rows
        return satisfy_x and satisfy_y

    def put(self, obj, x, y):
        """Put Agent obj to (x, y) and return True.
        Returns False when Agent is present, given invalid coordinate, obj not an Agent, or population capacity met.
        """
        if self.valid_coord(x, y):
            if isinstance(obj, Agent) and self.is_empty(x, y):
                obj.col = x
                obj.row = y
                self.get_cell(x, y).agent = obj
                #print(f"Put Agent {obj.id} at {obj.col, obj.row}, exp {x, y}")
                return True
        #print(f"WARNING: Failed to put Agent {obj.id} at {x, y}")
        return False

    def remove(self, x, y):
        """Remove the agent at (x, y) from the landscape. Does nothing when no agent is present."""
        if not self.is_empty(x, y):
            self.get_cell(x, y).agent = None
        else:
            #print(f"WARNING: Tried to remove nonexistent Agent at ({x, y})") # TODO Handle this better if it happens
            pass

    def is_empty(self, x, y): # Should refractor to a much better name
        """Check if (x, y) has an agent."""
        return self.landscape[y][x].agent == None

    def next_open(self):
        """Return next random open coordinate.
        Returns coordinates of an open cell. Returns None, None when full.
        """
        tries = 0
        maxTries = self.rows * self.cols
        x, y = 0, 0
        while tries < maxTries:
            tries += 1
            x = random.randint(0, self.cols - 1)
            y = random.randint(0, self.rows - 1)
            if self.is_empty(x, y):
                break
        return (x, y) if tries <= maxTries else (None, None)
    
    def get_cell(self, x, y):
        """Get the cell at (x, y).
        Since the landscape is a torus, coordinate values "wrap" around. Similar to pacman.
        """
        if self.valid_coord(x, y):
            return self.landscape[y % self.rows][x % self.cols]

    def move(self, x0, y0, x1, y1):
        """Move Agent at (x0, y0) to (x1, y1)."""
        oldCell = self.get_cell(x0, y0)
        if oldCell.agent == None:
            #print(f"WARNING: Tried to move nonexistent Agent at {x0, y0}") # TODO Fix this bug?
            return
        self.put(oldCell.agent, x1, y1)
        self.remove(x0, y0)

    def update_sugar(self, t):
        """Update all the sugar. t is the current time."""
        for y in range(self.rows):
            for x in range(self.cols):
                cell = self.get_cell(x, y)
                if cell.capacity > 0:
                    cell.update_sugar(self.t_lastSugarUpdate, t)
        self.t_lastSugarUpdate = t
