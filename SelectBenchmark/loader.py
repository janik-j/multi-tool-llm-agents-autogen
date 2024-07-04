import json
import os
from typing import Dict

def load_benchmark_suite(directory : str) -> Dict[str, Dict]:
    """Load a suite of benchmarks from a directory.
    Args:
        directory (str): The directory containing the benchmark files.
    Returns:
        dict: A dictionary containing the loaded benchmarks.
    """
    benchmark_files = [
        "calculator.json",
        "coding.json",
        "DALLE.json",
        "image_retriever.json",
        "pdf_parser.json",
        "web_retriever.json"
    ]
    benchmarks = {}
    for file_name in benchmark_files:
        file_path = os.path.join(directory, file_name)
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                key = os.path.splitext(file_name)[0]
                benchmarks[key] = data
            print(f"Successfully loaded {file_name}")
        except FileNotFoundError:
            print(f"Warning: {file_name} not found in the specified directory.")
        except json.JSONDecodeError:
            print(f"Error: {file_name} is not a valid JSON file.")
        except Exception as e:
            print(f"An error occurred while loading {file_name}: {str(e)}")
    
    return benchmarks


"""
# Example usage

working_dir = os.getcwd()
benchmark_directory = os.path.join(working_dir, "SelectBenchmark")
loaded_benchmarks = load_benchmark_suite(benchmark_directory)

# Accessing the data
for benchmark_name, benchmark_data in loaded_benchmarks.items():
    print(f"\nBenchmark: {benchmark_name}")
    print(f"Number of test cases: {len(benchmark_data.get('test_cases', []))}")
    
    if benchmark_data.get('test_cases'):
        first_test = benchmark_data['test_cases'][0]
        print(f"First test case: {first_test.get('name', 'N/A')}")
        print(f"Input: {first_test.get('input', 'N/A')}")
    else:
        print("No test cases found in this benchmark.")
"""