import math


class Event:
    MOVE = "move"
    DIE = "die"
    def __init__(self, time, type, agent):
        self.time = time
        self.type = type
        self.agent = agent


class EventCalendar:
    def __init__(self):
        self.calendar = []

    def add(self, event):
        self.calendar.append(event)

    def getMinEvent(self):
        """Pop the next minimum event (event with lowest event time)."""
        if len(self.calendar) > 0:
            minTime, minIndex = math.inf, math.inf
            for i in range(len(self.calendar)):
                event = self.calendar[i]
                if event.time < minTime:
                    minTime = event.time
                    minIndex = i
            return self.calendar.pop(minIndex)
        return None

    def remove_agent(self, agent):
        """Remove events relating to given Agent."""
        for i in range(self.calendar.count(agent)):
            self.calendar.remove(agent)
