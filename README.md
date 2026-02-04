# Agentic AI Image Generator

## Project Overview

This project implements an autonomous agent designed to generate high-quality, trend-aware imagery for platforms like Pinterest. By leveraging Large Language Models (LLMs) and image generation capabilities, the system operates as a "creative director," analyzing trends, formulating visual strategies, and producing optimized visual assets without constant human intervention.

The core functionality revolves around a two-step process:
1.  **Strategic Planning ("Brain"):** The system uses Google's Gemini models (via LangChain) to act as a creative strategist. It identifies high-performing topics, defines target audiences, and structures detailed visual concepts including lighting, composition, and color palettes.
2.  **Asset Generation:** Based on the strategy, the system generates prompts for high-fidelity image creation and handles the organization of these assets.

## Key Features

*   **Autonomous Trend Analysis:** Automatically identifies relevant and high-performing topics.
*   **Structured Creative Direction:** Generates comprehensive design breifs (JSON) covering SEO keywords, visual composition, and emotional tone.
*   **Automated Image Synthesis:**  Translates strategic briefs into detailed image generation prompts.
*   **Logging and Tracking:** Maintains detailed logs of strategies and generated assets for review and iteration.

## Technical Architecture

The project is built using Python and relies on the following key libraries:
*   **LangChain:** For orchestrating LLM interactions and maintaining structured output.
*   **Google Generative AI (Gemini):** Serves as the reasoning engine for creative strategy.
*   **Pydantic:** Ensures strict data validation and structured JSON outputs for reliability.
*   **Python-Dotenv:** Manages secure configuration and environment variables.

## structure

*   `AGENT/brain.ipynb`: The strategic core. This notebook contains the logic for the "Creative Director" agent, defining the prompts and schema for generating pin concepts.
*   `AGENT/image_gen.ipynb`: Handles the actual image generation workflows based on the strategies defined by the brain.
*   `main.py`: The entry point for executing the agentic workflow.
*   `rows`: Stores log files of daily operations.
*   `pinterest_images`: Directory where generated image assets are saved.

## Getting Started

### Prerequisites

Ensure you have Python installed on your system. You will also need API keys for the services used (e.g., Google Gemini, OpenAI).

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/sougata010/IMAGE_GEN_AGENTIC_AI.git
    ```
2.  Navigate to the project directory:
    ```bash
    cd IMAGE_GEN_AGENTIC_AI
    ```
3.  Install dependencies:
    (If using `uv` or `pip`)
    ```bash
    pip install -r requirements.txt
    ```
    *Note: If a requirements file is not present, ensure you install `langchain-google-genai`, `langchain-openai`, `pydantic`, and `python-dotenv`.*

### Configuration

Create a `.env` file in the root directory and add your API keys:

```env
GOOGLE_API_KEY=your_google_api_key
```

### Usage

Run the main script to trigger the agent:

```bash
python main.py
```

The system will generate a strategy JSON and proceed with the defined workflow. Check the `logs` directory for details on the execution and the `pinterest_images` folder for the output.

## Future Development

Future improvements may include direct integration with the Pinterest API for automated scheduling and publishing, as well as enhanced feedback loops to refine image generation quality based on engagement metrics.
