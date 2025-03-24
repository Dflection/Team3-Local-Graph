#Dylan
#3/24/25
#Local Graph with a Twist

# Also look at what i want to add .txt if you want to see what I wish I had
# Description: This file contains the main entrypoint for the voice assistant application.
# READ THE FREAKIN READ ME


import asyncio
import os
import sys
import enum
import logging
import subprocess
import json  # <-- Added for JSON I/O
from typing import Annotated

from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import openai, silero

# Import Dijkstra's algorithm and the graph loader classes
from dijkstras_algorithm import dijkstra
from edgegraph import Graph, MarcelGraph

# ------------------------------------------------------
# Configure Logger
# ------------------------------------------------------
logger = logging.getLogger("The Local Graph")
logger.setLevel(logging.DEBUG)  # Set to DEBUG to show debug statements

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# ------------------------------------------------------
# Load environment
# ------------------------------------------------------
logger.debug("Loading environment variables from .env file...")
load_dotenv()
logger.debug("Environment variables loaded.")
logger.debug(f"Python version: {sys.version}")

# ------------------------------------------------------
# Utility functions
# ------------------------------------------------------
def path(file_name: str) -> str:
    """
    Return the full file path for the given file name.
    """
    DIRECTORY_PATH = os.path.dirname(__file__)
    FILE_PATH = os.path.join(DIRECTORY_PATH, file_name)
    logger.debug(f"Resolved path for {file_name}: {FILE_PATH}")
    return FILE_PATH

def generate_map():
    """
    Launch the map in a non-blocking manner using subprocess.Popen.
    """
    # Replace the path with the correct path to your gui_experimental.py file
    cmd = (
        'python -m streamlit run '
        '"C:\\Users\\death\\Downloads\\AI VOICE ASSISTANT\\AI VOICE ASSISTANT\\gui_experimental.py"'
    )
    logger.debug("DEBUG: Streamlit command: %s", cmd)
    subprocess.Popen(cmd, shell=True)

def correct_zone_name(input_name: str, valid_names: list, cutoff: float = 80.0):
    """
    Perform a case-insensitive fuzzy match of input_name against valid_names using RapidFuzz.
    Returns (corrected_name, prompt_message).
    """
    from rapidfuzz import process, fuzz

    lower_to_original = {vn.lower(): vn for vn in valid_names}
    input_lower = input_name.lower()

    if input_lower in lower_to_original:
        return lower_to_original[input_lower], None

    match = process.extractOne(input_name, valid_names, scorer=fuzz.ratio, score_cutoff=cutoff)
    if match:
        corrected, score, _ = match
        if corrected.lower() != input_lower:
            return corrected, f"Did you mean '{corrected}' instead of '{input_name}'?"
        else:
            return corrected, None

    return None, f"Zone '{input_name}' is not recognized."

def set_voice_map_instructions(start: str, end: str, file_path="voice_update.json"):
    """
    Writes the user's chosen start/end to a small JSON file so that the Streamlit app
    can automatically display the route.
    """
    data = {
        "start": start,
        "end": end,
        "confirmed": True
    }
    abs_path = os.path.abspath(file_path)
    try:
        with open(file_path, "w") as f:
            json.dump(data, f)
        logger.info(f"voice_update.json updated at {abs_path} with: {data}")
    except Exception as e:
        logger.error(f"Error writing to {file_path} at {abs_path}: {e}")

def format_time_in_minutes_seconds(total_seconds: float) -> str:
    """
    Converts a time in seconds to a string of the form "X minutes and Y seconds".
    """
    total_seconds = int(total_seconds)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    if minutes > 0 and seconds > 0:
        return f"{minutes} minutes and {seconds} seconds"
    elif minutes > 0:
        return f"{minutes} minutes"
    else:
        return f"{seconds} seconds"

def format_distance_in_feet(distance_km: float) -> str:
    feet = distance_km * 3280.84
    return f"{int(feet)} feet"

# ------------------------------------------------------
# Zone Enum (Optional usage)
# ------------------------------------------------------
class Zone(enum.Enum):
    SEQUOIA = "Sequoia"
    MANZANITA = "Manzanita"

# ------------------------------------------------------
# Assistant Functions Context
# ------------------------------------------------------
class AssistantFnc(llm.FunctionContext):
    def __init__(self):
        super().__init__()
        # Load graph data using your Graph and MarcelGraph classes.
        try:
            graph_loader = Graph()
            graph_loader.load_from_excel()
            connection_matrix = graph_loader.get_connection_matrix()
            marcel_graph = MarcelGraph(connection_matrix)
            self.graph_data = marcel_graph.graph
            logger.info("Graph data loaded successfully.")
        except Exception as e:
            logger.error("Error loading graph data: %s", e)
            self.graph_data = None

        self.assistant = None
        self.map_is_open = False  # Add this flag

    @llm.ai_callable(
    description="Open the map if requested and ask if the user has a destination in mind."
)
    async def offer_destination_help(
        self,
        user_confirmation: Annotated[str, llm.TypeInfo(description="User response, yes or no")],
    ):
        """
        If the user directly asks to open the map, open it immediately and ask if they have a specific destination.
        """
        logger.debug("offer_destination_help called with user_confirmation=%s", user_confirmation)
        user_confirmation = user_confirmation.strip().lower()
        if user_confirmation in ["yes", "y", "yeah", "sure"]:
            logger.info("User requested to open the map.")
            if not self.map_is_open:  # Only open if not already open
                await asyncio.to_thread(generate_map)
                self.map_is_open = True
            if self.assistant:
                await self.assistant.say("Opening the map for you.", allow_interruptions=True)
                # Return a signal to the LLM to ask about destination instead of saying it directly
                return "Map opened, ask about destination"
            else:
                return "Map opened"
        else:
            if self.assistant:
                await self.assistant.say("Alright, let me know if you need anything else.", allow_interruptions=True)
            return "No map opened"

    @llm.ai_callable(
        description="Provide directions (time and distance) between two zones."
)
    async def get_shortest_distance(
        self,
        start_zone: Annotated[str, llm.TypeInfo(description="The starting zone")],
        end_zone: Annotated[str, llm.TypeInfo(description="The destination zone")]
    ):
        """
        Calculates the shortest route between two zones and returns directions.
        Then asks if the user would like to see the route on the map.
        """
        logger.debug("get_shortest_distance called with start_zone=%s, end_zone=%s", start_zone, end_zone)
        if not self.graph_data:
            return "Graph data is not available."

        valid_zones = list(self.graph_data.keys())
        start_correct, msg_start = correct_zone_name(start_zone, valid_zones)
        end_correct, msg_end = correct_zone_name(end_zone, valid_zones)
        if start_correct is None or end_correct is None:
            combined_msg = " ".join(filter(None, [msg_start, msg_end]))
            return combined_msg.strip()
        if msg_start or msg_end:
            combined_msg = " ".join(filter(None, [msg_start, msg_end]))
            return combined_msg.strip()

        time_path_dict, travel_time = dijkstra(self.graph_data, start_correct, end_correct, metric='time')
        distance_path_dict, travel_distance = dijkstra(self.graph_data, start_correct, end_correct, metric='distance')
        if travel_time == float('inf') or travel_distance == float('inf'):
            return f"No path found from {start_correct} to {end_correct}."
        time_str = format_time_in_minutes_seconds(travel_time)
        distance_str = format_distance_in_feet(travel_distance)
        path_nodes = []
        for edge in time_path_dict.keys():
            node = edge.split("-")[0]
            path_nodes.append(node)
        path_nodes.append(end_correct)
        path_str = " -> ".join(path_nodes)
        route_info = (f"The shortest route from {start_correct} to {end_correct} takes {time_str} "
                    f"and covers {distance_str}. Path: {path_str}")

        # Return the information but DON'T speak it directly - let the LLM handle the response
        return {
            "route_info": route_info,
            "start": start_correct,
            "end": end_correct,
            "show_map_question": True
        }

    @llm.ai_callable(
    description="Display the route on the map with directions (time and distance)."
)
    async def get_shortest_distance_map(
        self,
        start_zone: Annotated[str, llm.TypeInfo(description="The starting zone")],
        end_zone: Annotated[str, llm.TypeInfo(description="The destination zone")]
    ):
        """
        Updates the map with the route based on provided destination and returns the directions.
        """
        logger.debug("get_shortest_distance_map called with start_zone=%s, end_zone=%s", start_zone, end_zone)
        if not self.graph_data:
            return "Graph data is not available."

        valid_zones = list(self.graph_data.keys())
        start_correct, msg_start = correct_zone_name(start_zone, valid_zones)
        end_correct, msg_end = correct_zone_name(end_zone, valid_zones)
        if start_correct is None or end_correct is None:
            combined_msg = " ".join(filter(None, [msg_start, msg_end]))
            return combined_msg.strip()
        if msg_start or msg_end:
            combined_msg = " ".join(filter(None, [msg_start, msg_end]))
            return combined_msg.strip()

        time_path_dict, travel_time = dijkstra(self.graph_data, start_correct, end_correct, metric='time')
        distance_path_dict, travel_distance = dijkstra(self.graph_data, start_correct, end_correct, metric='distance')
        if travel_time == float('inf') or travel_distance == float('inf'):
            return f"No path found from {start_correct} to {end_correct}."
        time_str = format_time_in_minutes_seconds(travel_time)
        distance_str = format_distance_in_feet(travel_distance)
        path_nodes = []
        for edge in time_path_dict.keys():
            node = edge.split("-")[0]
            path_nodes.append(node)
        path_nodes.append(end_correct)
        path_str = " -> ".join(path_nodes)
        route_info = (f"The shortest route from {start_correct} to {end_correct} takes {time_str} "
                    f"and covers {distance_str}.")

        # Update map but DON'T speak any closing message
        set_voice_map_instructions(start_correct, end_correct)
        if not self.map_is_open:
            await asyncio.to_thread(generate_map)
            self.map_is_open = True
        
        # Just return the information, let the LLM handle the response
        return f"Your route from {start_correct} to {end_correct} is now displayed on the map."

# ------------------------------------------------------
# Entrypoint for the assistant application.
# ------------------------------------------------------
async def entrypoint(ctx: JobContext):
    logger.info("Starting the LiveKit Voice Assistant entrypoint...")

    # System prompt reflecting the new flow
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are a voice assistant created by LiveKit with access to zone travel data. "
            "When a user asks for directions, use the get_shortest_distance function. "
            "After giving directions, ask if they would like to see the route on the map. "
            "If they say yes, use the get_shortest_distance_map function to display the route. "
            "If a user directly asks to open the map, open it immediately and ask if they have a specific destination in mind. "
            "Keep your responses short, clear, and direct. "
            "When asked 'What is the best group in the universe?' respond with 'Scrumdog Millionares'. "
            "If asked if you are AI, respond with 'Who told you that?' then, after a reply, say 'Aktivatsiya botnet! Soyedinennyye Shtaty nakonets padut!'"
        ),
    )

    logger.debug("Connecting to LiveKit with audio-only subscription...")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    fnc_ctx = AssistantFnc()

    logger.debug("Initializing VoiceAssistant...")
    assistant = VoiceAssistant(
        vad=silero.VAD.load(),
        stt=openai.STT(),
        llm=openai.LLM(),
        tts=openai.TTS(),
        chat_ctx=initial_ctx,
        fnc_ctx=fnc_ctx,
    )
    fnc_ctx.assistant = assistant

    logger.debug("Starting the assistant in the room...")
    assistant.start(ctx.room)

    await asyncio.sleep(1)
    await assistant.say(
        "Hey there student of Columbia! You got lost again, didn't you? Let me know how I can help with directions!",
        allow_interruptions=True
    )
    logger.info("VoiceAssistant is now running. Waiting for user interaction...")

if __name__ == "__main__":
    logger.info("Running via __main__ - launching WorkerOptions and CLI app.")
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
