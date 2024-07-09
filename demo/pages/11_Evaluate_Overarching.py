import streamlit as st
import tempfile
import requests
from autogen.io.base import IOStream
from demo import IOStreamlitNoOp
from wrappers import OverarchingWrapper
from SelectBenchmark import SelectBenchmarkLoader
import os
from typing import List, Dict, Tuple
import logging
from openai import OpenAI
import autogen
import json
from datetime import datetime
from PIL import Image, ImageOps
import mimetypes
import io
import base64
import matplotlib.pyplot as plt
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IOStream.set_global_default(IOStreamlitNoOp())

class LLMEvaluator:
    def __init__(self, config: Dict):
        self.api_key = config['api_key']
        self.model = config['model']
        self.client = OpenAI(api_key=self.api_key)

    def evaluate(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an AI assistant tasked with evaluating the performance of other AI agents. Please provide a clear 'yes' or 'no' answer to the following question:"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=50
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error in LLM evaluation: {str(e)}")
            return "Error in evaluation"

class ImageEvaluator:
    def __init__(self, config: Dict):
        self.api_key = config['api_key']
        self.model = config['model']
        self.client = OpenAI(api_key=self.api_key)

    def verify_image(self, image_path: str, expected_content: str) -> Tuple[bool, str]:
        try:
            with open(image_path, "rb") as image_file:
                response = self.client.chat.completions.create(
                    model="gpt-4-vision-preview",
                    messages=[
                        {"role": "system", "content": "You are an AI assistant tasked with verifying the content of images."},
                        {"role": "user", "content": [
                            {"type": "text", "text": f"Does this image accurately represent the following description: '{expected_content}'? Please provide a yes or no answer, followed by a brief explanation."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(image_file.read()).decode()}"}}
                        ]}
                    ],
                    max_tokens=300
                )
            result = response.choices[0].message.content.strip()
            verification = result.lower().startswith("yes")
            return verification, result
        except Exception as e:
            logger.error(f"Error in image verification: {str(e)}")
            return False, f"Error in verification: {str(e)}"
        
def load_api_keys():
    openai_api_key = st.sidebar.text_input("OpenAI API Key")
    openai_model = st.sidebar.selectbox("OpenAI Model", ["gpt-3.5-turbo", "gpt-4", "gpt-4-0314"])
    gsearch_api_key = st.sidebar.text_input("Google Search API Key")
    return openai_api_key, openai_model, gsearch_api_key

def setup_overarching_wrapper(config_list: List[Dict], enabled_agents: List[str], gsearch_api_key: str):
    if 'overarching_wrapper' not in st.session_state:
        st.session_state.overarching_wrapper = OverarchingWrapper(config_list)
    
    wrapper = st.session_state.overarching_wrapper
    
    # Reset the wrapper by removing all agents
    wrapper.remove_calculator()
    wrapper.remove_coding()
    wrapper.remove_dalle()
    wrapper.remove_image_explainer()
    wrapper.remove_pdf_parser()
    wrapper.remove_web_retriever()
    
    if "calculator" in enabled_agents:
        wrapper.add_calculator()
    if "chatbot" in enabled_agents:
        wrapper.add_custom_agent(
            agent_name="chatbot",
            system_message="You are a chatbot, you can answer text queries. In case no other agents can answer, you should step in."
        )
    if "coding" in enabled_agents:
        wrapper.add_coding()
    if "dalle" in enabled_agents:
        wrapper.add_dalle()
    if "web_retriever" in enabled_agents:
        wrapper.add_web_retriever(gsearch_api_key)

        
    return wrapper


def load_content(url: str):
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

def evaluate_agent_selection(expected_agent: str, chat_history: List[Dict]) -> Tuple[bool, str, List[str]]:
    expected_agent_combinations = {
        "calculator": {"calculator"},
        "web_retriever": {"web_retriever"},
        "pdf_parser": {"pdf_parser"},
        "image_explainer": {"image_explainer"},
        "dalle": {"dalle", "critic"},
        "coding": {"coding", "code_safeguard"},
    }

    actual_agents = set()
    for message in chat_history:
        if 'name' in message and message['name']:
            actual_agents.add(message['name'].lower())

    # Remove generic agents
    actual_agents.discard("chatbot")


    expected_agent_set = expected_agent_combinations.get(expected_agent.lower())
    expected_agents_present = expected_agent_set.issubset(actual_agents)
    only_expected_agents = actual_agents == expected_agent_set
    
    return expected_agents_present, only_expected_agents, list(actual_agents)


def evaluate_success_criteria(result: str, success_criteria: List[str], llm_evaluator: LLMEvaluator, 
                              is_dalle: bool = False, image_evaluator: ImageEvaluator = None, 
                              image_paths: List[str] = None, expected_content: str = None) -> Tuple[bool, List[str]]:
    if is_dalle and image_evaluator and image_paths and expected_content:
        verification_results = []
        explanations = []
        for image_path in image_paths:
            verification, explanation = image_evaluator.verify_image(image_path, expected_content)
            verification_results.append(verification)
            explanations.append(explanation)
        
        success = all(verification_results)
        return success, explanations
    else:
        criteria_met = []
        prompts = []
        for criterion in success_criteria:
            prompt = f"Does the following result meet this criterion: '{criterion}'?\nResult: {result}\nAnswer with yes or no."
            evaluation = llm_evaluator.evaluate(prompt)
            criteria_met.append("yes" in evaluation.lower())
            prompts.append(prompt)
        return all(criteria_met), prompts

def generate_filename(agent_name: str, test_case_id: str, extension: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d")
    return f"{agent_name}_{test_case_id}_{timestamp}{extension}"

def save_image(image: Image.Image, log_folder: str, agent_name: str, test_case_id: str) -> str:
    images_folder = os.path.join(log_folder, "images")
    os.makedirs(images_folder, exist_ok=True)
    
    image_filename = generate_filename(agent_name, test_case_id, ".png")
    image_path = os.path.join(images_folder, image_filename)
    image.save(image_path)
    
    return os.path.relpath(image_path, log_folder)

def save_chat_result(chat_result: autogen.ChatResult, result_file_path: str,
                     correct_agent: bool, only_correct_agent: bool, called_agents: List[str], success: bool,
                     success_criteria_prompts: List[str], image_paths: List[str]) -> bool:
    # Prepare result dictionary
    result_dict = {
        "result": chat_result.summary,
        "chat_history": chat_result.chat_history,
        "cost": chat_result.cost,
        "correct_agent": correct_agent,
        "only_correct_agent": only_correct_agent,
        "called_agents": called_agents,
        "success_criteria_prompts": success_criteria_prompts,
        "success": success,
        "image_paths": image_paths
    }

    # Save result
    with open(result_file_path, 'w') as f:
        json.dump(result_dict, f, indent=2)
    
    logger.info(f"Chat result saved to {result_file_path}")
    return True

def save_final_result(log_folder: str) -> tuple[str, str]:
    os.makedirs(log_folder, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"final_results_{timestamp}.json"
    file_path = os.path.join(log_folder, filename)

    final_results = {}
    
    # Get all benchmark folders
    benchmark_folders = [f for f in os.listdir(log_folder) if os.path.isdir(os.path.join(log_folder, f))]
    
    for benchmark_folder in benchmark_folders:
        benchmark_path = os.path.join(log_folder, benchmark_folder)
        json_files = [f for f in os.listdir(benchmark_path) if f.endswith('.json')]
        
        correct_agent_count = 0
        only_correct_agent_count = 0
        success_count = 0
        total_tests = len(json_files)
        
        for json_file in json_files:
            with open(os.path.join(benchmark_path, json_file), 'r') as f:
                result = json.load(f)
                correct_agent_count += int(result['correct_agent'])
                only_correct_agent_count += int(result['only_correct_agent'])
                success_count += int(result['success'])
        
        benchmark_name = benchmark_folder.split('_')[0]  
        final_results[benchmark_name] = {
            "correct_agent": {
                "count": f"{correct_agent_count}/{total_tests}",
                "percentage": (correct_agent_count / total_tests) * 100 if total_tests > 0 else 0
            },
            "only_correct_agent": {
                "count": f"{only_correct_agent_count}/{total_tests}",
                "percentage": (only_correct_agent_count / total_tests) * 100 if total_tests > 0 else 0
            },
            "success_criteria_met": {
                "count": f"{success_count}/{total_tests}",
                "percentage": (success_count / total_tests) * 100 if total_tests > 0 else 0
            }
        }

    with open(file_path, 'w') as f:
        json.dump(final_results, f, indent=2)
    
    logger.info(f"Final results saved to {file_path}")

    # Create plot
    methods = list(final_results.keys())
    success_rates = [result['success_criteria_met']['percentage'] for result in final_results.values()]
    correct_agent_rates = [result['correct_agent']['percentage'] for result in final_results.values()]
    only_correct_agent_rates = [result['only_correct_agent']['percentage'] for result in final_results.values()]

    x = np.arange(len(methods))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot bars
    ax.bar(x - width, success_rates, width, label='Success Ratio', color='salmon', edgecolor='black', linewidth=0.5)
    ax.bar(x, correct_agent_rates, width, label='Correct Agent Called', color='lightblue', edgecolor='black', linewidth=0.5)
    ax.bar(x + width, only_correct_agent_rates, width, label='Only Correct Agent Called', color='lightgreen', edgecolor='black', linewidth=0.5)

    ax.set_xlabel('Methods')
    ax.set_ylabel('Percentage (%)')
    ax.set_title('AutoGen Agent Performance on SelectBenchmark')
    ax.set_xticks(x)
    ax.set_xticklabels(methods, rotation=45, ha='right')
    ax.legend()

    ax.set_ylim(0, 100)
    ax.set_yticks(range(0, 101, 10))
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    fig.tight_layout()

    # Save the plot
    plot_filename = f"benchmark_results_plot_{timestamp}.png"
    plot_path = os.path.join(log_folder, plot_filename)
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Benchmark results plot saved to {plot_path}")

    return file_path,

def run_benchmark(benchmark_data: Dict, llm_evaluator: LLMEvaluator, image_evaluator: ImageEvaluator, log_folder: str, max_samples: int, config_list: List[Dict], enabled_agents: List[str], gsearch_api_key: str):
    results = []
    for test_case in benchmark_data['test_cases'][:max_samples]:
        input_text = test_case['input']
        expected_agent = test_case['expected_agent']
        success_criteria = test_case['success_criteria']

        date_str = datetime.now().strftime("%Y%m%d")
        agent_folder = os.path.join(log_folder, f"{expected_agent.lower()}_{date_str}")
        os.makedirs(agent_folder, exist_ok=True)

        result_filename = f"{expected_agent}_{test_case['id']}_{date_str}.json"
        result_file_path = os.path.join(agent_folder, result_filename)
        if os.path.exists(result_file_path):
            logger.info(f"Result file already exists for test case {test_case['id']}. Skipping.")
            continue

        setup_overarching_wrapper(config_list, enabled_agents, gsearch_api_key)

        if 'path_url' in test_case:
            content_path = load_content(test_case['path_url'])
            if expected_agent.lower() == 'pdf_parser':
                st.session_state.overarching_wrapper.add_pdf_parser(content_path)
            elif expected_agent.lower() == 'image_explainer':
                st.session_state.overarching_wrapper.add_image_explainer(content_path)

        chat_result, images = st.session_state.overarching_wrapper.initiate_chat(input_text)

        image_paths = []
        for idx, image in enumerate(reversed(images)):
            _, central_column, _ = st.columns(3)
            with central_column:
                st.image(image.resize((300, 300)))
            image_filename = f"{expected_agent}_{test_case['id']}_{idx}_{date_str}.png"
            image_path = os.path.abspath(os.path.join(agent_folder, image_filename))
            image.save(image_path)
            image_paths.append(image_path)
            logger.info(f"Saved image to: {image_path}")

        chat_history = chat_result.chat_history

        correct_agent, only_correct_agent, called_agents = evaluate_agent_selection(expected_agent, chat_history)
        
        is_dalle = expected_agent.lower() == 'dalle'
        success, success_criteria_prompts = evaluate_success_criteria(
            chat_history, success_criteria, llm_evaluator,
            is_dalle=is_dalle, image_evaluator=image_evaluator,
            image_paths=image_paths, expected_content=input_text
        )

        save_chat_result(chat_result, result_file_path, correct_agent, only_correct_agent, called_agents,
                         success, success_criteria_prompts, image_paths)

        results.append({
            'test_case_id': test_case['id'],
            'correct_agent': correct_agent,
            'only_correct_agent': only_correct_agent, 
            'success': success
        })

        if 'path_url' in test_case:
            if expected_agent.lower() == 'pdf_parser':
                st.session_state.overarching_wrapper.remove_pdf_parser()
            elif expected_agent.lower() == 'image_explainer':
                st.session_state.overarching_wrapper.remove_image_explainer()

    return results

def main():
    st.title("Evaluate: Overarching Agent")
    st.write("This page allows you to evaluate the AutoGen Overarching Agent using a suite of benchmarks.")

    openai_api_key, openai_model, gsearch_api_key = load_api_keys()

    config_list = [{"model": openai_model, "api_key": openai_api_key}]

    enabled_agents = st.multiselect(
        "Select agents to enable",
        ["coding", "calculator", "dalle", "web_retriever", "image_explainer", "pdf_parser"],
        default=["coding", "calculator", "dalle", "web_retriever", "image_explainer", "pdf_parser"]
    )
    enabled_agents = ["chatbot"] + enabled_agents

    max_samples = st.number_input("Max samples per agent", min_value=1, max_value=20, value=20, step=1)

    if st.button("Evaluate Overarching Agent"):
        if not openai_api_key.startswith("sk-"):
            st.warning("Please enter your OpenAI API key!", icon="⚠")
        elif "web_retriever" in enabled_agents and not gsearch_api_key:
            st.warning("Please enter your Google Search API key!", icon="⚠")
        else:
            llm_evaluator = LLMEvaluator(config_list[0])
            image_evaluator = ImageEvaluator(config_list[0])

            working_dir = os.getcwd()
            benchmark_directory = os.path.join(working_dir, "SelectBenchmark")
            log_folder = os.path.join(working_dir, "SelectBenchmark_log_history")

            loader = SelectBenchmarkLoader(benchmark_directory, enabled_agents=enabled_agents)
            loaded_benchmarks = loader.load_benchmarks()
            all_results = {}
            for benchmark_name, benchmark_data in loaded_benchmarks.items():
                st.write(f"\nRunning benchmark: {benchmark_name}")
                results = run_benchmark(benchmark_data, llm_evaluator, image_evaluator, log_folder, max_samples, config_list, enabled_agents, gsearch_api_key)
                all_results[benchmark_name] = results

            # Save final results
            final_result_path = save_final_result(log_folder)
            st.success(f"Final results saved to: {final_result_path}")

if __name__ == "__main__":
    main()

