import os
import json
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import logging
from openai import OpenAI
import base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SelectBenchmarkEvaluator:
    def __init__(self, log_folder: str, config: Dict):
        self.log_folder = log_folder
        self.config = config
        self.client = OpenAI(api_key=config['api_key'])

    def evaluate_llm(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.config['model'],
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

    def evaluate_agent_selection(self, expected_agent: str, chat_history: List[Dict]) -> Tuple[bool, bool, List[str]]:
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

        expected_agent_set = expected_agent_combinations.get(expected_agent.lower(), set())
        expected_agents_present = expected_agent_set.issubset(actual_agents)
        only_expected_agents = actual_agents == expected_agent_set
        
        return expected_agents_present, only_expected_agents, list(actual_agents)

    def evaluate_success_criteria(self, result: str, success_criteria: List[str], 
                                  is_dalle: bool = False, image_paths: List[str] = None, 
                                  expected_content: str = None) -> Tuple[bool, List[str]]:
        if is_dalle and image_paths and expected_content:
            verification_results = []
            explanations = []
            for image_path in image_paths:
                verification, explanation = self.verify_image(image_path, expected_content)
                verification_results.append(verification)
                explanations.append(explanation)
            
            success = all(verification_results)
            return success, explanations
        else:
            criteria_met = []
            prompts = []
            for criterion in success_criteria:
                prompt = f"Does the following result meet this criterion: '{criterion}'?\nResult: {result}\nAnswer with yes or no."
                evaluation = self.evaluate_llm(prompt)
                criteria_met.append("yes" in evaluation.lower())
                prompts.append(prompt)
            return all(criteria_met), prompts

    def save_chat_result(self, chat_result, result_file_path: str,
                         correct_agent: bool, only_correct_agent: bool, called_agents: List[str], success: bool,
                         success_criteria_prompts: List[str], image_paths: List[str]) -> bool:
        # Prepare result dictionary
        result_dict = {
            "result": chat_result.summary if hasattr(chat_result, 'summary') else str(chat_result),
            "chat_history": chat_result.chat_history if hasattr(chat_result, 'chat_history') else [],
            "cost": chat_result.cost if hasattr(chat_result, 'cost') else None,
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

    def save_final_result(self) -> Tuple[str, str]:
        os.makedirs(self.log_folder, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"final_results_{timestamp}.json"
        file_path = os.path.join(self.log_folder, filename)

        final_results = {}
        
        # Get all benchmark folders
        benchmark_folders = [f for f in os.listdir(self.log_folder) if os.path.isdir(os.path.join(self.log_folder, f))]
        
        for benchmark_folder in benchmark_folders:
            benchmark_path = os.path.join(self.log_folder, benchmark_folder)
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
        plot_path = os.path.join(self.log_folder, plot_filename)
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Benchmark results plot saved to {plot_path}")

        return file_path, plot_path