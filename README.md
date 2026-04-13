**Title:**
Generate Network Information using GenAI API

**Members:**
Via Alexa Yu, Aliana Santos, Dhruvanshi Patel

**Description:**
Develop an application that integrates with a Generative AI (GenAI) such as LLaMA, DeepSeek or similar AI systems using an API. The application will use AI to intelligently generate additional rows of data based on patterns it identifies in a or more given table(s). These generated rows will then be appended to the original dataset and
saved automatically. The application should have the following features:

* The application will receive one or more table(s) containing network information or dataset.
* Sample dataset will be provided for developing and testing.
* The AI will analyze the structure, schema, and content of the provided dataset.
* The AI will generate new, contextually relevant rows based on the input data.
* The generated rows should be coherent, valid within the schema, and enhance the dataset without duplicating existing entries.
* The newly generated rows should then be appended to the original table automatically.
* Save the table.
* Provide one or more mechanism(s) to preview and validate AI-generated rows before final insertion.

**Installation:**
1. Download and install Ollama from https://ollama.com/download/windows
2. Download the LLaMA model by opening a terminal and running:
```
ollama pull llama3.2:1b
```
3. Create a virtual environment by opening a terminal inside the project folder:
```
python -m venv venv
venv\Scripts\activate
```
4. Install dependencies by typing into the terminal:
```
venv\Scripts\pip install pandas requests scipy numpy
```
5. Run `main.py`