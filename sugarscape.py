# An implementation of the "sugarscape" somewhat based on Chapters I-III
# in the book "Growing Artificial Societies: Social Science from The Bottom Up"
# by Epstein, Axell
from agent import AgentList
from config import SEED, SHOW_SUGAR, ROWS, COLUMNS, SHOW_FINAL_COMPARISON,\
    SHOW_ANIMATION, SHOW_TERRAIN, AGENTS, MAX_T, PAUSE
from event import EventCalendar, Event
from landscape import Landscape
from pause import interpret
import random
from visual import str_map, compare_maps, nice_statistics


random.seed(SEED)

landscape = Landscape(ROWS, COLUMNS)
eventList = EventCalendar()
agentList = AgentList(AGENTS, landscape, eventList)

print(f"Seed: {SEED}")
print(nice_statistics(agentList, 0))
init_map = str_map(landscape, showSugar=SHOW_SUGAR)

e = eventList.getMinEvent()
t = e.time
while t < MAX_T and len(eventList.calendar) > 0:
    # Update sugar in the landscape
    landscape.update_sugar(t)

    if e.type == Event.MOVE:
        e.agent.move(t, landscape, eventList)
    elif e.type == Event.DIE:
        e.agent.alive = False
        agentList.remove(e.agent, eventList, landscape)
    elif e.type == Event.BIRTH:
        baby = e.agent.birth(t, landscape, eventList)
        if baby:
            agentList.full_add(baby, landscape)
    elif e.type == Event.REPRODUCE:
        e.agent.reproduce(t, landscape, eventList)

    if SHOW_ANIMATION and t >= 0: # Weird bug where sometimes negative times are shown?
        bMap = str_map(landscape, showSugar=SHOW_SUGAR)
        print(f"t = {t}, alive = {len(agentList.agentList)}\n{bMap}")

    if PAUSE:
        # Print nice statistics and await input
        # Empty input == continue to next event
        print(nice_statistics(agentList, t))
        repeatInput = True
        while repeatInput:
            uInput = input(f"Input t={t}> ")
            repeatInput = interpret(uInput, agentList, eventList, landscape, t)

    if len(eventList.calendar) > 0:
        e = eventList.getMinEvent()
        t = e.time

# Statistics output
print(nice_statistics(agentList, t))

if SHOW_FINAL_COMPARISON:
    final_map = str_map(landscape, showSugar=SHOW_SUGAR)
    print(f"Comparison of initial (t=0) and final maps (t={t}), respectively:")
    # Assuming numberLines=True, adds 1 to rows and cols
    rows = ROWS + 1
    cols = COLUMNS + 1
    compared = compare_maps(init_map, final_map, rows, cols)
    print(compared)
if SHOW_TERRAIN:
    print("Terrain:")
    print(str_map(landscape, terrain=True))
