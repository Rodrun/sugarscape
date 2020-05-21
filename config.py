from os import environ
from distutils import util
sbool = util.strtobool
get = environ.get

# Important general config
MAX_T = float(get("MAX_T", 200)) # Maximum simulation time
SEED = get("SEED", "1234567890") # Random seed
ALPHA = float(get("ALPHA", .33)) # How many units of sugar regrow per timestep (1.0 unit of time)
#BETA = 2 # Interval of time of which ALPHA sugar units regrows during the winter
#GAMMA = 50 # Length of a season period
ROWS = int(get("ROWS", 50)) # Landscape rows
COLUMNS = int(get("COLUMNS", 50)) # Landscape columns
AGENTS = int(get("AGENTS", 400)) # Initial agent population size
MAX_POSSIBLE_SUGAR = int(get("MAX_POSSIBLE_SUGAR", 5)) # Maximum possible sugar capacity per cell
MAX_HEIGHT = int(get("MAX_HEIGHT", 4)) # Maximum cell height
# Visual general config
SHOW_ANIMATION = sbool(get("SHOW_ANIMATION", "False")) # Show visual of every event -- slower simulation
SHOW_FINAL_COMPARISON = sbool(get("SHOW_FINAL_COMPARISON", "False")) # Show visual comparison of initial state vs final state
SHOW_SUGAR = sbool(get("SHOW_SUGAR", "False")) # Show sugar in visual
SHOW_TERRAIN = sbool(get("SHOW_TERRAIN", "False")) # Show cell heights in a separate visual
# Plot general config
SHOW_PLOTS = sbool(get("SHOW_PLOTS", "False")) # Show the plot of various statistics at the end
PLOTS = get("PLOTS", "wealth,population") # Comma-separated list of plots to show
# Specific visual chars config
AGENT_HEALTHY_CHAR = get("AGENT_HEALTHY_CHAR", "O") # Agent with sugar > metabolic rate
AGENT_CRITICAL_CHAR = get("AGENT_CRITICAL_CHAR", "o") # Agent with sugar <= metabolic rate
SUGAR_0_CHAR = get("SUGAR_0_CHAR", "․") # Sugar at (0, 25)% max height
SUGAR_1_CHAR = get("SUGAR_1_CHAR", "⁚") # Sugar at [25, 50)% max height
SUGAR_2_CHAR = get("SUGAR_2_CHAR", "⁝") # Sugar at [50, 75)% max height
SUGAR_3_CHAR = get("SUGAR_3_CHAR", "⁞") # Sugar at [75, 100]% max height
TERR_0_CHAR = get("TERR_0_CHAR", "▁") # Cell at [0, 25)% max height
TERR_1_CHAR = get("TERR_1_CHAR", "▃") # Cell at [25, 50)% max height
TERR_2_CHAR = get("TERR_2_CHAR", "▅") # Cell at [50, 75)% max height
TERR_3_CHAR = get("TERR_3_CHAR", "▇") # Cell at [75, 100%] max height
