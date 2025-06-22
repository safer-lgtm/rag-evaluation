## 🧠 RAG Evaluation – Project Overview

In many real-world applications, fast and accurate access to domain-specific knowledge is essential. Retrieval-Augmented Generation (RAG) combines Large Language Models (LLMs) with document retrieval to improve factual accuracy and domain relevance. This project focuses on building an automated framework for evaluating the output quality of RAG-based systems.

### 📊 Methodology

* **Data Pipeline**

    * Ingest and preprocess unstructured internal documents
    * Embed text into vector representations
    * Store in a Databricks-hosted vector index

* **Retrieval Layer**

    * Evaluate multiple retrieval strategies (semantic, keyword, hybrid)

* **LLM Generation**

    * Generate responses by prompting LLMs (e.g., GPT-4, Claude, LLaMA) with retrieved context passages

* **Evaluation Framework**

    * Automatic scoring using metrics such as:

        * *Context Precision*, *Context Recall*, *Faithfulness*, *Answer Relevance*
    * Integrate LLM-as-a-Judge for scalable, reference-free evaluation

* **Experiment Management**

    * Use MLflow to track and version all experiments


### 🔧 Environment Setup


#### Getting Started
0. **Set Environment**

    ```bash
    python -m venv venv
    source venv/bin/activate   # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

1. **Install the Databricks CLI**
   Follow the instructions at:
   👉 [https://docs.databricks.com/dev-tools/cli/databricks-cli.html](https://docs.databricks.com/dev-tools/cli/databricks-cli.html)
    Or easily use Chocolatey:
   👉 [https://community.chocolatey.org/packages/databricks-cli]
    
    Run this to insure databricks-cli is installed 

    ```bash
    databricks --version
    ```

2. **Authenticate with your Databricks workspace:**
   Run the following in your terminal:

   ```bash
   databricks configure
   ```

3. **Deploy the development environment:**

   ```bash
   databricks bundle deploy --target dev
   ```

Add this to your `environment.yml`

#### **Python dependencies**

```yaml
name: rag-eval
channels:
  - defaults
dependencies:
  - python=3.10
  - pip
  - pip:
      - databricks-sdk
      - mlflow
      - openai
      - langchain
      - beautifulsoup4
```