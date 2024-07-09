import streamlit as st
from autogen.io.base import IOStream
from demo import IOStreamlitNoOp
from wrappers import OverarchingWrapper
from SelectBenchmark import SelectBenchmarkLoader, SelectBenchmarkEvaluator
import os
from typing import List, Dict, Any
import logging
from openai import OpenAI
import autogen
from datetime import datetime
from PIL import Image
import base64
import requests
import PyPDF2
import io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IOStream.set_global_default(IOStreamlitNoOp())

def load_api_keys():
    openai_api_key = st.sidebar.text_input("OpenAI API Key")
    openai_model = st.sidebar.selectbox("OpenAI Model", ["gpt-3.5-turbo", "gpt-4", "gpt-4-0314", "gpt-4o-2024-05-13"])
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

def evaluate_vanilla_gpt4o(prompt: str, config: Dict, input_type: str = 'text', input_data: Any = None) -> Dict:
    client = OpenAI(api_key=config['api_key'])
    try:
        messages = [{"role": "system", "content": "You are a helpful assistant."}]

        if input_type == 'text':
            messages.append({"role": "user", "content": prompt})
        elif input_type == 'image':
            buffered = io.BytesIO()
            Image.open(input_data).save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{img_str}"
                        }
                    }
                ]
            })
        elif input_type == 'pdf':
            pdf_content = ""
            with open(input_data, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    pdf_content += page.extract_text()
            
            messages.append({"role": "user", "content": f"{prompt}\n\nPDF Content:\n{pdf_content}"})
        elif input_type == 'image_generation':
            # For image generation, we'll use DALL-E 3
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            image_url = response.data[0].url
            # Download the image
            image_response = requests.get(image_url)
            if image_response.status_code == 200:
                return {"type": "image", "content": image_response.content}
            else:
                return {"type": "error", "content": f"Failed to download image: {image_response.status_code}"}
        # For text, image analysis, and PDF
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.1,
            max_tokens=1000
        )
        return {"type": "text", "content": response.choices[0].message.content.strip()}

    except Exception as e:
        return {"type": "error", "content": f"Error in GPT-4o evaluation: {str(e)}"}


def run_benchmark(benchmark_data: Dict, evaluator: SelectBenchmarkEvaluator, log_folder: str, max_samples: int, config_list: List[Dict], enabled_agents: List[str], gsearch_api_key: str, evaluation_mode: str):
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

        if evaluation_mode == "multiagent":
            setup_overarching_wrapper(config_list, enabled_agents, gsearch_api_key)

            if 'path' in test_case:
                if expected_agent.lower() == 'pdf_parser':
                    st.session_state.overarching_wrapper.add_pdf_parser(test_case['path'])
                elif expected_agent.lower() == 'image_explainer':
                    st.session_state.overarching_wrapper.add_image_explainer(test_case['path'])

            chat_result, images = st.session_state.overarching_wrapper.initiate_chat(input_text)
        if evaluation_mode == "gpt-4o":
            logger.info(f"Running vanilla GPT-4o evaluation for test case {test_case['id']}")
            st.write(f"Running vanilla GPT-4o evaluation for test case {test_case['id']}")
            input_type = 'text'
            input_data = None
            if expected_agent.lower() == 'image_explainer':
                input_type = 'image'
                input_data = test_case.get('path')
            elif expected_agent.lower() == 'pdf_parser':
                input_type = 'pdf'
                input_data = test_case.get('path')
            elif expected_agent.lower() == 'dalle':
                input_type = 'image_generation'

            result = evaluate_vanilla_gpt4o(input_text, config_list[0], input_type, input_data)
            if result['type'] == 'image':
                if isinstance(result['content'], str):  # It's a URL
                    image_response = requests.get(result['content'])
                    if image_response.status_code == 200:
                        image = Image.open(io.BytesIO(image_response.content))
                    else:
                        st.error(f"Failed to download image: {image_response.status_code}")
                        continue
                else:  # It's already bytes
                    image = Image.open(io.BytesIO(result['content']))
                
                image_filename = f"{expected_agent}_{test_case['id']}_{date_str}.png"
                image_path = os.path.join(agent_folder, image_filename)
                image.save(image_path)
                chat_result = autogen.ChatResult(chat_history=[
                    {"role": "user", "content": input_text},
                    {"role": "assistant", "content": f"Image generated and saved as {image_filename}"}
                ])
                images = [image]
            else:
                chat_result = autogen.ChatResult(chat_history=[
                    {"role": "user", "content": input_text},
                    {"role": "assistant", "content": result['content']}
                ])
                images = []

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

        if evaluation_mode == "multiagent":
            correct_agent, only_correct_agent, called_agents = evaluator.evaluate_agent_selection(expected_agent, chat_result.chat_history)
        else:
            correct_agent, only_correct_agent, called_agents = False, False, []

        is_dalle = expected_agent.lower() == 'dalle'
        success, success_criteria_prompts = evaluator.evaluate_success_criteria(
            chat_result.chat_history, success_criteria,
            is_dalle=is_dalle, image_paths=image_paths, expected_content=input_text
        )

        evaluator.save_chat_result(chat_result, result_file_path, correct_agent, only_correct_agent, called_agents,
                                   success, success_criteria_prompts, image_paths)

        results.append({
            'test_case_id': test_case['id'],
            'correct_agent': correct_agent,
            'only_correct_agent': only_correct_agent, 
            'success': success
        })

        if evaluation_mode == "multiagent" and 'path' in test_case:
            if expected_agent.lower() == 'pdf_parser':
                st.session_state.overarching_wrapper.remove_pdf_parser()
            elif expected_agent.lower() == 'image_explainer':
                st.session_state.overarching_wrapper.remove_image_explainer()

    return results

def main():
    st.title("Evaluate: Overarching Agent")
    st.write("This page allows you to evaluate the AutoGen Overarching Agent or vanilla GPT-4o using a suite of benchmarks.")

    openai_api_key, openai_model, gsearch_api_key = load_api_keys()

    config_list = [{"model": openai_model, "api_key": openai_api_key}]

    evaluation_mode = st.radio(
        "Select evaluation mode",
        ("Autogen Multiagent", "Vanilla GPT-4o")
    )

    enabled_agents = []
    enabled_agents = st.multiselect(
        "Select agents/functionalities to benchmark",
        ["coding", "calculator", "dalle", "web_retriever", "image_explainer", "pdf_parser"],
        default=["coding", "calculator", "dalle", "web_retriever", "image_explainer", "pdf_parser"]
    )
    enabled_agents = ["chatbot"] + enabled_agents

    max_samples = st.number_input("Max samples per agent", min_value=1, max_value=20, value=20, step=1)

    if st.button("Run Evaluation"):
        if not openai_api_key.startswith("sk-"):
            st.warning("Please enter your OpenAI API key!", icon="⚠")
        elif evaluation_mode == "Autogen Multiagent" and "web_retriever" in enabled_agents and not gsearch_api_key:
            st.warning("Please enter your Google Search API key!", icon="⚠")
        else:
            st.write("Starting evaluation...")
            selected_mode = "multiagent" if evaluation_mode == "Autogen Multiagent" else "vanilla_gpt-4o"
            working_dir = os.getcwd()
            benchmark_directory = os.path.join(working_dir, "SelectBenchmark")
            log_folder = os.path.join(working_dir, f"SelectBenchmark_logs_{selected_mode}")

            loader = SelectBenchmarkLoader(benchmark_directory, enabled_agents=enabled_agents)
            loaded_benchmarks = loader.load_benchmarks()

            evaluator = SelectBenchmarkEvaluator(log_folder, config_list[0])

            all_results = {}
            for benchmark_name, benchmark_data in loaded_benchmarks.items():
                st.write(f"\nRunning benchmark: {benchmark_name}")
                results = run_benchmark(benchmark_data, evaluator, log_folder, max_samples, config_list, enabled_agents, gsearch_api_key, 
                                        "multiagent" if evaluation_mode == "Autogen Multiagent" else "gpt-4o")
                all_results[benchmark_name] = results

            # Save final results
            final_result_path, plot_path = evaluator.save_final_result()
            st.success(f"Final results saved to: {final_result_path}")
            st.image(plot_path, caption="Benchmark Results Plot")

if __name__ == "__main__":
    main()

