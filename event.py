import math
import simulus


class Event:
    MOVE = "move"
    DIE = "die"
    REPRODUCE = "reproduce"
    BIRTH = "birth"

    def __init__(self, time, type, agent, callback):
        self.time = time
        self.type = type
        self.agent = agent
        self.callback = callback


class EventCalendar:
    def __init__(self):
        self.sim = simulus.simulator()
        self.pre = None # Pre-event function
        self.pre_args = None
        self.post = None # Post-event function
        self.post_args = None

    def now(self):
        """Get the current simulation time."""
        return self.sim.now

    def set_preevent(self, callback, *args):
        """Set the pre-event operation.
        callback - Callable to be called before event executes.
        args - Arguments to be passed into callback.
        """
        if not callable(callback):
            raise TypeError("set_preevent() requires callable argument")
        self.pre = callback
        self.pre_args = args

    def set_postevent(self, callback, *args):
        """Set the post-event operation.
        callback - Callable to be called after event executes.
        kwargs - Argument sto be passed into callback.
        """
        if not callable(callback):
            raise TypeError("set_postevent() requires callable argument")
        self.post = callback
        self.post_args = args

    def add(self, event):
        return self.sim.sched(event.callback, until=event.time, name=event.type)

    def run(self, until):
        """Run the simulation until given time."""
        while self.sim.now <= until:
            self.pre(*self.pre_args)
            self.sim.step()
            self.post(*self.post_args)
            if self.sim.peek() == math.inf:
                print("No more events to execute. Simulation completed before max time.")
                break

    def resched(self, e, newTime):
        """Reschedule event to newTime.
        e - The return value from add() (More specifically the return value of simulus.simulator.sched()).
        newTime - The new time to reschedule, should be >= now().
        Returns rescheduled event (from simulus.simulator.resched()), None if could not reschedule.
        """
        return self.sim.resched(e, until=newTime)

    def cancel(self, e):
        """Cancel an event. Does not do anything if e is None or an already occurred event.
        e - The return value of add().
        """
        if e != None:
            self.sim.cancel(e)

    def cancels(self, *es):
        """Cancel multiple events. This is just a loop of cancel().
        es - Events to cancel. (return value of add(), resched()).
        """
        for ev in es:
            self.cancel(ev)

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
