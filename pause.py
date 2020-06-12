# Pause input handling
# Every input command function takes in the following arguments:
# args - List of arguments after invoking the command
# agentList - AgentList of current state
# eventCalendar - EventCalendar of current state
# landscape - Landscape of current state
# time - Current time
import traceback
from visual import str_agent, str_cell, str_map, compare_maps, str_event
import re


########## Input command functions ##########
def help(args, agentList, eventCalendar, landscape, time):
    if len(args) == 0:
        print(list(COMMANDS.keys()))
    else:
        cmdName = args[0]
        if cmdName in COMMANDS:
            cmd = COMMANDS[cmdName]
            cmdFormat = cmd["format"]
            cmdSumm = cmd["summary"]
            print(f"{args[0]} {cmdFormat}\n{cmdSumm}")
        else:
            print(f"Unknown command name '{cmdName}'.")


def cell(args, agentList, eventCalendar, landscape, time):
    if len(args) == 0:
        help("cell", agentList, eventCalendar, landscape, time)
    elif len(args) == 2:
        try:
            x, y = int(args[0]), int(args[1])
            target = landscape.get_cell(x, y)
            if target:
                print(str_cell(target))
        except Exception as err:
            print(f"An error occurred: {err}\n{traceback.format_exc()}")
    else:
        print("Invalid arguments; help cell")


def agent(args, agentList, eventCalendar, landscape, time):
    if len(args) == 0:
        help("agent", agentList, eventCalendar, landscape, time)
    elif len(args) == 1:
        try:
            id = int(args[0])
            target = agentList.get_by_id(id)
            if target:
                print(str_agent(target))
            else:
                print(f"Could not find Agent {id}")
        except Exception as err:
            print(f"An error occurred: {err}\n{traceback.format_exc()}")
    else:
        print("Invalid arguments; help agent")


def visualize(args, agentList, eventCalendar, landscape, time):
    print(f"{str_map(landscape)}\n{str_map(landscape, terrain=True)}")


def alive(args, agentList, eventCalendar, landscape, time):
    for agent in list(agentList.agentList):
        print(agent.id)


def lscount(args, agentList, eventCalendar, landscape, time):
    ct = 0
    for y in range(landscape.rows):
        for x in range(landscape.cols):
            if landscape.get_cell(y, x).agent != None:
                ct += 1
    print(f"Landscape count: {ct}")


########### Base commands ###########
COMMANDS = {
    "help": {
        "summary": "Display available commands and summaries",
        "format": "[command name]",
        "exec": help
    },
    "cell": {
        "summary": "Get specific cell info",
        "format": "<x> <y>",
        "exec": cell
    },
    "agent": {
        "summary": "Get specific agent info",
        "format": "<id>",
        "exec": agent
    },
    "visualize": {
        "summary": "Show all visuals of the current state",
        "format": "",
        "exec": visualize
    },
    "alive": {
        "summary": "Show all alive Agent IDs",
        "format": "",
        "exec": alive
    },
    "lscount": {
        "summary": "Show the population count of the landscape",
        "format": "",
        "exec": lscount
    }
}


########## Business logic ##########
def interpret(command, agentList, eventCalendar, landscape, time):
    """Interpret given command string.
    Returns True when non-blank command/input given. 
    """
    parsed = re.compile("\s").split(command)
    if len(parsed) == 0 or command.strip().replace("\s", "") == "":
        return False
    cmdName = parsed[0]
    args = parsed[1:]
    if cmdName in COMMANDS:
        COMMANDS[cmdName]["exec"](args, agentList, eventCalendar, landscape, time)
    else:
        print(f"Unknown command '{cmdName}'; type 'help' for a list of commands")
    return True
