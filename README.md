# Multi-Agent Large Language Models with AutoGen

This project was completed by Janik Jehkul, Nikita Kostin, and Xiangyu Ning under the supervision of Johann Hagerer as
a part of the NLP Lab course.

## Motivation

An agent is an entity acting on behalf of human intent, capable of conversation and interaction with other agents. 

Empirical studies demonstrate an advantage of a multi-agent setup over the traditional single-agent approach. This
project is based on the paper "Autogen: Enabling next-gen llm applications via multi-agent conversation framework." by
Wu, Qingyun, et al. and serves as a demonstration of such multi-agent approaches.

## Overview

As a part of this project we

1. Conducted the experiments presented in the original paper to reproduce the findings. Their results are located in the
`experiment_results` folder.
2. Explored further scenarios in which the multi-agent setup would be beneficial, such as PDF parsing or DALL-E image
generation.
3. Built a parent (overarching) agent to combine the standalone agents using a group chat for answering a broader range
of questions.
4. Developed a demo using the `Streamlit` Python library for showcasing the internal discussion process for both
standalone agents and the parent agent.
5. Created a custom `SelectBenchmark` for evaluating the frequency of the calls to correct agents and automated the
evaluation process using the LLM-as-evaluator approach.

## Future work

1. Integrate more agents into the parent agent flow.
2. Fine-tune the specialized agents to get better results for specific tasks.
3. Compare the performance of our agents with similar frameworks.
