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

def evaluate_agent_selection(expected_agent: str, chat_history: List[Dict], llm_evaluator: LLMEvaluator) -> Tuple[bool, str]:
    actual_agent = None
    for message in chat_history:
        if message.get('name') and message.get('name').lower() == expected_agent.lower():
            actual_agent = message['name']
            break
    
    if actual_agent is None:
        actual_agent = "Unknown"
    
    prompt = f"Was the correct agent selected and used? Expected: {expected_agent.lower()}, Actual: {actual_agent.lower()}. Answer with yes or no."
    evaluation = llm_evaluator.evaluate(prompt)
    return "yes" in evaluation.lower(), prompt

def evaluate_success_criteria(result: str, success_criteria: List[str], llm_evaluator: LLMEvaluator) -> Tuple[bool, List[str]]:
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

def save_chat_result(chat_result: autogen.ChatResult, log_folder: str, test_case_id: str, 
                     correct_agent: bool, success: bool, agent_selection_prompt: str, 
                     success_criteria_prompts: List[str], agent_name: str, image_urls: List[str]):
    os.makedirs(log_folder, exist_ok=True)
    filename = generate_filename(agent_name, test_case_id, ".json")
    file_path = os.path.join(log_folder, filename)
    
    result_dict = {
        "result": chat_result.summary,
        "chat_history": chat_result.chat_history,
        "cost": chat_result.cost,
        "agent_selection_prompt": agent_selection_prompt,
        "correct_agent": correct_agent,
        "success_criteria_prompts": success_criteria_prompts,
        "success": success,
        "image_urls": image_urls
    }
    
    with open(file_path, 'w') as f:
        json.dump(result_dict, f, indent=2)
    
    logger.info(f"Chat result saved to {file_path}")

def run_benchmark(benchmark_data: Dict, llm_evaluator: LLMEvaluator, log_folder: str, max_samples: int):
    results = []
    for test_case in benchmark_data['test_cases'][:max_samples]:
        input_text = test_case['input']
        expected_agent = test_case['expected_agent']
        success_criteria = test_case['success_criteria']

        if 'path_url' in test_case:
            content_path = load_content(test_case['path_url'])
            print("Content path: ", content_path)
            print("Expected agent: ", expected_agent)
            if expected_agent.lower() == 'pdf_parser':
                st.session_state.overarching_wrapper.add_pdf_parser(content_path)
            elif expected_agent.lower() == 'image_explainer':
                st.session_state.overarching_wrapper.add_image_explainer(content_path)
        print("PDF: " + str(st.session_state.overarching_wrapper.is_pdf_attached))
        print("Image: " + str(st.session_state.overarching_wrapper.image_path))
        chat_result, images = st.session_state.overarching_wrapper.initiate_chat(input_text)

        image_urls = []
        for idx, image in enumerate(reversed(images)):
            _, central_column, _ = st.columns(3)
            with central_column:
                st.image(image.resize((300, 300)))
            image_url = save_image(image, log_folder, expected_agent, f"{test_case['id']}_{idx}")
            image_urls.append(image_url)
    
        chat_history = chat_result.chat_history
        print("DALLE chat result: ", chat_result)

        correct_agent, agent_selection_prompt = evaluate_agent_selection(expected_agent, chat_history, llm_evaluator)
        success, success_criteria_prompts = evaluate_success_criteria(chat_history, success_criteria, llm_evaluator)

        save_chat_result(chat_result, log_folder, test_case['id'], correct_agent, success, 
                         agent_selection_prompt, success_criteria_prompts, expected_agent, image_urls)

        results.append({
            'test_case_id': test_case['id'],
            'correct_agent': correct_agent,
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

    max_samples = st.number_input("Max samples per agent", min_value=1, value=5, step=1)

    if st.button("Evaluate Overarching Agent"):
        if not openai_api_key.startswith("sk-"):
            st.warning("Please enter your OpenAI API key!", icon="⚠")
        elif "web_retriever" in enabled_agents and not gsearch_api_key:
            st.warning("Please enter your Google Search API key!", icon="⚠")
        else:
            setup_overarching_wrapper(config_list, enabled_agents, gsearch_api_key)
            llm_evaluator = LLMEvaluator(config_list[0])

            working_dir = os.getcwd()
            benchmark_directory = os.path.join(working_dir, "SelectBenchmark")
            log_folder = os.path.join(working_dir, "SelectBenchmark_log_history")

            loader = SelectBenchmarkLoader(benchmark_directory, enabled_agents=enabled_agents)
            loaded_benchmarks = loader.load_benchmarks()

            all_results = {}
            for benchmark_name, benchmark_data in loaded_benchmarks.items():
                st.write(f"\nRunning benchmark: {benchmark_name}")
                results = run_benchmark(benchmark_data, llm_evaluator, log_folder, max_samples)
                all_results[benchmark_name] = results

            # Display results
            for benchmark_name, results in all_results.items():
                st.write(f"\nResults for {benchmark_name}:")
                correct_agent_count = sum(r['correct_agent'] for r in results)
                success_count = sum(r['success'] for r in results)
                total_tests = len(results)
                
                st.write(f"Correct agent selection: {correct_agent_count}/{total_tests}")
                st.write(f"Success criteria met: {success_count}/{total_tests}")

if __name__ == "__main__":
    main()

