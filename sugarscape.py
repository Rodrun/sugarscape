# An implementation of the "sugarscape" somewhat based on Chapters I-III
# in the book "Growing Artificial Societies: Social Science from The Bottom Up"
# by Epstein, Axell
from agent import AgentList
from config import SEED, SHOW_SUGAR, ROWS, COLUMNS, SHOW_FINAL_COMPARISON,\
    SHOW_ANIMATION, SHOW_TERRAIN, AGENTS, MAX_T, PAUSE
from event import EventCalendar, Event
from landscape import Landscape
from pause import interpret
from rng import RNG
from visual import str_map, compare_maps, nice_statistics


def preoperation(lScape, calendar):
    lScape.update_sugar(calendar.now())


def postoperation(landscape, calendar, agentList):
    t = calendar.now()
    if SHOW_ANIMATION:
        bMap = str_map(landscape, showSugar=SHOW_SUGAR)
        print(f"t = {t}, alive = {len(agentList.agentList)}\n{bMap}")

    if PAUSE:
        # Print nice statistics and await input
        # Empty input == continue to next event
        print(nice_statistics(agentList, t))
        repeatInput = True
        while repeatInput:
            uInput = input(f"Input t={t}> ")
            repeatInput = interpret(uInput, agentList, calendar, landscape, calendar.now())


rng = RNG(SEED)
eventList = EventCalendar()
landscape = Landscape(ROWS, COLUMNS, rng=rng)
agentList = AgentList(AGENTS, landscape, eventList, rng=rng)

eventList.set_preevent(preoperation, landscape, eventList)
eventList.set_postevent(postoperation, landscape, eventList, agentList)

## Pre simulation ##
print(f"Seed: {SEED}")
print(nice_statistics(agentList, 0))
init_map = str_map(landscape, showSugar=SHOW_SUGAR)

## Simulation ##
eventList.run(MAX_T)

## Post simulation ##
t = eventList.now()
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
