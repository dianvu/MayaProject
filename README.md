# Prompting LLMs for Financial Transaction Analysis

This project leverage Language Models (LLMs) system to transform financial transactions into executive summary and tailored recommendations.

## Project Structure

```
.
├── app.py                 # Streamlit web application
├── main.ipynb            # Main analysis notebook
├── requirements.txt      # Project dependencies
├── clustering/          # Clustering analysis modules
├── data/               # Processed data storage
├── evaluations/        # Model evaluation results
├── features/          # Feature engineering modules
├── model/            # Model implementation
├── prompts/          # LLM prompt templates
├── raw_data/         # Raw input data
└── utils/            # Utility functions
```

## Prerequisites

- Python 3.11+
- An Anthropic API key (for Claude LLM)

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd PromptingLLMs
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the project root and add your Anthropic API key:
```
ANTHROPIC_API_KEY=your_api_key_here
```

## Usage

### Running the Web Application

To start the Streamlit web interface:
```bash
streamlit run app.py
```

### Running the Analysis Notebook

Open `main.ipynb` in Jupyter Notebook or JupyterLab