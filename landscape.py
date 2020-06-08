from agent import Agent
from config import MAX_HEIGHT, MAX_POSSIBLE_SUGAR, ALPHA
import random


class Cell:
    """The bones of the Landscape: every coordinate is an individual Cell."""
    def __init__(self, x, y, rng):
        self.x = x
        self.y = y
        self.capacity = rng.get("cell").integers(0, MAX_POSSIBLE_SUGAR + 1)
        self.sugar = self.capacity
        self.level = rng.get("cell").integers(1, MAX_HEIGHT + 1) # Synonymous with height
        self.agent = None

    def update_sugar(self, tLast, tNow):
        """Update the sugar count. tLast is the last time the count was updated, tNow is current time."""
        self.sugar = self.compute_sugar(tLast, tNow)

    def compute_sugar(self, tNow, tFuture):
        """Compute the amount of sugar the cell is expected to have by tFuture."""
        diff = tFuture - tNow
        computed = diff * ALPHA
        total = self.sugar + computed
        if total > self.capacity:
            return self.capacity
        return total


class Landscape:
    """The world that hosts Cells that hold Agents and sugar."""
    def __init__(self, rows, cols, rng):
        self.rows = rows
        self.cols = cols
        self.rng = rng
        self.landscape = [[Cell(x, y, rng) for x in range(self.cols)] for y in range(self.rows)]
        self.t_lastSugarUpdate = 0

    def convert_coords(self, x, y):
        """Convert the given coordinates to list-usable indexes."""
        return x % self.cols, y % self.rows

    def put(self, obj, x, y):
        """Put Agent obj to (x, y) and return True on success.
        Returns False when Agent is present, obj not an Agent, or population capacity met.
        """
        if isinstance(obj, Agent) and self.is_empty(x, y):
            obj.col = x
            obj.row = y
            self.get_cell(x, y).agent = obj
            return True
        else:
            print(f"WARNING: Could not put given {obj} at {x, y}!")
        return False

    def remove(self, x, y):
        """Remove the agent at (x, y) from the landscape. Does nothing when no agent is present."""
        if not self.is_empty(x, y):
            self.get_cell(x, y).agent = None
        else:
            #print(f"WARNING: Tried to remove nonexistent Agent at ({x, y})") # TODO Handle this better if it happens
            pass

    def is_empty(self, x, y):
        """Check if Cell at (x, y) does not have agent."""
        return self.get_cell(x, y).agent == None

    def next_open(self):
        """Return next random open coordinate.
        Returns coordinates of an open cell. Returns None, None when full.
        """
        tries = 0
        maxTries = self.rows * self.cols
        x, y = 0, 0
        while tries < maxTries:
            tries += 1
            x = self.rng.get("landscape").integers(0, self.cols)
            y = self.rng.get("landscape").integers(0, self.rows)
            if self.is_empty(x, y):
                break
        return (x, y) if tries <= maxTries else (None, None)
    
    def get_cell(self, x, y, strict=False):
        """Get the cell at (x, y).
        Since the landscape is a torus, coordinate values "wrap" around. Similar to pacman.
        """
        return self.landscape[y % self.rows][x % self.cols]

    def move(self, x0, y0, x1, y1):
        """Move Agent at (x0, y0) to (x1, y1)."""
        oldCell = self.get_cell(x0, y0)
        if oldCell.agent == None:
            #print(f"WARNING: Tried to move nonexistent Agent at {x0, y0}") # TODO Handle this better?
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
