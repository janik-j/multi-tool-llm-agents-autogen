import json
import logging
import mimetypes
import os
import tempfile
from typing import Dict, List
import requests
import io
import PIL.Image as Image

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SelectBenchmarkLoader:
    def __init__(self, directory: str, enabled_agents: List[str]):
        self.directory = directory
        self.enabled_agents = [agent.lower() for agent in enabled_agents]  # Ensure case-insensitive comparison

    def read_json_file(self, file_path: str) -> dict:
        """Read a JSON file and return its content."""
        with open(file_path, 'r') as file:
            return json.load(file)

    def load_content(self, url: str) -> str:
        """Load content from a given URL and return a temporary file path."""
        response = requests.get(url)
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '').split(';')[0]
            file_extension = mimetypes.guess_extension(content_type) or ".tmp"
            
            content = response.content

            if content_type.startswith('image/'):
                image = Image.open(io.BytesIO(content))
                original_format = image.format
                
                if image.width > 1000 or image.height > 1000:
                    image.thumbnail((1000, 1000))
                
                tmp_file = tempfile.NamedTemporaryFile(mode="wb", suffix=file_extension, delete=False)
                image.save(tmp_file.name, format=original_format)

                return tmp_file.name
            else:
                tmp_file = tempfile.NamedTemporaryFile(mode="wb", suffix=file_extension, delete=False)
                tmp_file.write(content)
                tmp_file.close()
                
                return tmp_file.name
        else:
            raise Exception(f"Failed to load content from {url}. Status code: {response.status_code}")

    def process_test_case(self, test_case: Dict) -> Dict:
        """Process a single test case, loading content for URLs."""
        if 'path_url' in test_case:
            try:
                test_case['path'] = self.load_content(test_case['path_url'])
                logger.info(f"Loaded content for {test_case['path_url']}")
            except Exception as e:
                logger.error(f"Failed to load content for {test_case['path_url']}: {str(e)}")
        return test_case

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
                    benchmark_data = self.read_json_file(file_path)
                    # Process each test case in the benchmark
                    benchmark_data['test_cases'] = [self.process_test_case(test_case) for test_case in benchmark_data['test_cases']]
                    benchmarks[key] = benchmark_data
                    logger.info(f"Successfully loaded and processed {file_name}")
                except FileNotFoundError:
                    logger.warning(f"{file_name} not found in the specified directory.")
                except json.JSONDecodeError:
                    logger.error(f"{file_name} is not a valid JSON file.")
                except Exception as e:
                    logger.error(f"An error occurred while loading {file_name}: {str(e)}")
        return benchmarks
        
