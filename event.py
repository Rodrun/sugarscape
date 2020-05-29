import math


class Event:
    MOVE = "move"
    DIE = "die"
    REPRODUCE = "reproduce"
    BIRTH = "birth"
    def __init__(self, time, type, agent):
        self.time = time
        self.type = type
        self.agent = agent


class EventCalendar:
    def __init__(self):
        self.calendar = []

    def add(self, event):
        self.calendar.append(event)

    def getMinEvent(self, doPop=True):
        """Get the next minimum event (event with lowest event time).
        doPop - Pop from event list if True.
        """
        if len(self.calendar) > 0:
            minTime, minIndex = math.inf, math.inf
            for i in range(len(self.calendar)):
                event = self.calendar[i]
                if event.time < minTime:
                    minTime = event.time
                    minIndex = i
            if doPop:
                return self.calendar.pop(minIndex)
            else:
                return self.calendar[minIndex]
        return None

    def remove_agent(self, agent):
        """Remove events relating to given Agent."""
        for i in range(self.calendar.count(agent)):
            self.calendar.remove(agent)

    def next_by_type(self, type):
        """Find the next event with given type.
        Returns next event, None if not found.
        """
        if len(self.calendar) > 0:
            minTime, minEvent = math.inf, None
            for event in self.calendar:
                if event.time < minTime and event.type == type:
                    minEvent = event
                    minTime = event.time
            return minEvent
        return None
