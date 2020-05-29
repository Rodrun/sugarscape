from agent import AgentList
import config as cfg
import math

def str_map(land, numberLines=True, showSugar=True, terrain=False):
    """Stringify the given landscape.
    If terrain = True, will give a map of terrain ONLY (no agents, sugar).
    """
    strMap = ""

    for row in range(land.rows):
        for col in range(land.cols):
            cell = land.get_cell(col, row)
            character = " " # Space = empty cell if not terrain map
            if not terrain:
                if cell.agent != None: # Agent prioritized over sugar
                    if cell.agent.sugar > cell.agent.metab:
                        character = cfg.AGENT_HEALTHY_CHAR
                    else:
                        character = cfg.AGENT_CRITICAL_CHAR
                elif cell.sugar > 0 and showSugar:
                    percentage = math.ceil(100 * (cell.level / cell.capacity))
                    if percentage < 25:
                        character = cfg.SUGAR_0_CHAR
                    elif percentage >= 25 and percentage < 50:
                        character = cfg.SUGAR_1_CHAR
                    elif percentage >= 50 and percentage < 75:
                        character = cfg.SUGAR_2_CHAR
                    elif percentage >= 75:
                        character = cfg.SUGAR_3_CHAR
            else: # Terrain-only map
                percentage = math.ceil(100 * (cell.level / cfg.MAX_HEIGHT))
                if percentage < 25:
                    character = cfg.TERR_0_CHAR
                elif percentage >= 25 and percentage < 50:
                    character = cfg.TERR_1_CHAR
                elif percentage >= 50 and percentage < 75:
                    character = cfg.TERR_2_CHAR
                elif percentage >= 75:
                    character = cfg.TERR_3_CHAR
            strMap += character

        if numberLines:
            strMap += str(row)[-1]
        strMap += "\n"
    
    if numberLines:
        for x in range(land.cols):
            strMap += str(x)[-1]
        strMap += " "
    return strMap


def compare_maps(sMap0, sMap1, rows, cols):
    """Get a neat string of a comparison of two str_map results. Assuming both have same dimensions."""
    str = ""
    for y in range(rows):
        startIndex = (y * cols) + y
        left = sMap0[startIndex:startIndex+cols]
        right = sMap1[startIndex:startIndex+cols]
        str += left + right + "\n"
    return str


def nice_statistics(aList, time):
    """Get a nicely formatted string of nice statistics of the given AgentList."""
    result = f"=====Agent statistics at t = {time}=====\n"
    result += f"Population: {len(aList.agentList)}\n"
    for stat in [AgentList.SUGAR, AgentList.METABOLISM, AgentList.VISION]:
        # Label ending
        ending = ""
        if stat == AgentList.SUGAR:
            ending += "sugar"
        elif stat == AgentList.METABOLISM:
            ending += "metabolism"
        elif stat == AgentList.VISION:
            ending += "vision"
        # Compute
        result += f"Average {ending}: {aList.average(stat)}\n"
        result += f"Median {ending}: {aList.median(stat)}\n"
    return result


def str_cell(cell):
    """Get a nice string of given Cell statistics."""
    result = f"-----Cell ({cell.x}, {cell.y})-----\n"
    result += f"sugar: {cell.sugar}\n"
    result += f"max sugar: {cell.capacity}\n"
    result += f"height/level: {cell.level}\n"
    result += f"Occupied by Agent {cell.agent.id if cell.agent else None}\n"
    return result


def str_agent(agent):
    """Get a nice string of an Agent's current state."""
    result = f"-----Agent {agent.id} ({agent.col}, {agent.row})-----\n"
    result += f"sugar: {agent.sugar}\n"
    result += f"metabolism: {agent.metab}\n"
    result += f"vision: {agent.vision}\n"
    result += f"t_nextEventTime: {agent.t_nextEventTime}\n"
    result += f"t_nextEventType: {agent.t_nextEventType}\n"
    result += f"period_g: {agent.period_g}\n"
    if agent.mate:
        result += f"mate: {agent.mate.id}"
    return result


def str_event(event):
    """Get a nice string of an Event."""
    result = f"-----Event @ t={event.time}\n"
    result += f"type: {event.type}\n"
    result += f"agent: {event.agent.id}\n"
    return result
