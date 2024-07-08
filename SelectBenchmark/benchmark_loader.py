import os
import json
from typing import Dict
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SelectBenchmarkLoader:
    def __init__(self, directory: str, enabled_agents: list):
        self.directory = directory
        self.enabled_agents = [agent.lower() for agent in enabled_agents]  # Ensure case-insensitive comparison

    def read_json_file(self, file_path: str) -> dict:
        """Read a JSON file and return its content."""
        with open(file_path, 'r') as file:
            return json.load(file)

    def load_benchmarks(self) -> Dict[str, Dict]:
        """Load a suite of benchmarks from a directory, filtering based on enabled agents."""
        benchmarks = {}
        all_files = os.listdir(self.directory)
        for file_name in all_files:
            agent_name = os.path.splitext(file_name)[0].lower()
            if agent_name in self.enabled_agents:
                file_path = os.path.join(self.directory, file_name)
                key = os.path.splitext(file_name)[0]
                try:
                    benchmarks[key] = self.read_json_file(file_path)
                    logger.info(f"Successfully loaded {file_name}")
                except FileNotFoundError:
                    logger.warning(f"{file_name} not found in the specified directory.")
                except json.JSONDecodeError:
                    logger.error(f"{file_name} is not a valid JSON file.")
                except Exception as e:
                    logger.error(f"An error occurred while loading {file_name}: {str(e)}")
        
        return benchmarks