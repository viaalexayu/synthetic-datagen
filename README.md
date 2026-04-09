# Generate Network Information using GenAI API

**Course Project — Networking**

|               |                                               |
| ------------- | --------------------------------------------- |
| **Members**   | Via Alexa Yu, Aliana Santos, Dhruvanshi Patel |
| **AI Model**  | LLaMA 3.2 (via Ollama)                        |
| **Framework** | Streamlit                                     |
| **Language**  | Python                                        |

---

## Project Description

This application integrates with **LLaMA 3.2**, a local Generative AI model running via Ollama, to intelligently generate synthetic rows of BGP network data. The AI analyses the structure, schema, and content of a provided dataset and generates new, contextually relevant rows that are coherent, valid within the schema, and do not duplicate existing entries. Generated rows can be previewed and validated before being appended to the original dataset and saved.

---

## Features

- Upload one or more BGP network CSV tables
- AI analyses the schema, column types, and data patterns
- Generates new rows that are contextually relevant and schema-valid
- Validation layer checks every AI-generated row before insertion
- Preview table with checkboxes — approve or reject individual rows
- Approved rows are automatically appended to the original dataset
- Download the expanded dataset as a new CSV file
- Runs entirely locally — no internet connection required after setup

---

## Requirements

- Windows 10 or 11
- Python 3.9 or higher
- At least 8 GB RAM
- ~2 GB free disk space (for the LLaMA model)

---

## Installation

### 1. Install Ollama

Download and install Ollama from https://ollama.com/download/windows

After installation, Ollama runs automatically in your system tray.

### 2. Pull the LLaMA model

Open a terminal and run:

```bash
ollama pull llama3.2:1b
```

Verify the model downloaded successfully:

```bash
ollama list
```

You should see `llama3.2:1b` in the list.

### 3. Download the project

Place the project folder on your computer, for example:

```
C:\Users\yourname\Desktop\synthetic-datagen\
```

### 4. Create a virtual environment

Open a terminal inside the project folder:

```bash
python -m venv venv
venv\Scripts\activate
```

Your terminal prompt should now show `(venv)`.

### 5. Install dependencies

```bash
venv\Scripts\pip install -r requirements.txt
```

**requirements.txt** contains:

```
streamlit
pandas
requests
```

---

## Running the Application

### Step 1 — Verify Ollama is running

Open your browser and go to:

```
http://localhost:11434
```

You should see: `Ollama is running`

If not, open a terminal and run:

```bash
ollama serve
```

### Step 2 — Start the app

In your terminal with `(venv)` active:

```bash
venv\Scripts\python -m streamlit run app.py
```

The app opens automatically in your browser at:

```
http://localhost:8501
```

---

## How to Use

| Step | Action                                         |
| ---- | ---------------------------------------------- |
| 1    | Upload your `BGP Network dataset.csv` file     |
| 2    | Set how many rows you want to generate (1–50)  |
| 3    | Click **Generate rows** and wait ~1–2 minutes  |
| 4    | Review the generated rows in the preview table |
| 5    | Uncheck any rows you want to discard           |
| 6    | Click **Download BGP_expanded.csv**            |

---

## Project Structure

```
synthetic-datagen/
├── app.py                      # Streamlit UI — all 4 stages
├── ollama_service.py           # LLaMA API calls and batch logic
├── validator.py                # Row validation — 7 rules
├── requirements.txt            # Python dependencies
├── BGP Network dataset.csv     # Original dataset
└── README.md                   # This file
```

### File responsibilities

| File                | Responsibility                                                 |
| ------------------- | -------------------------------------------------------------- |
| `app.py`            | The entire frontend — upload, preview, approve, download       |
| `ollama_service.py` | Builds the prompt, calls LLaMA in batches, repairs JSON        |
| `validator.py`      | Validates every generated row against 7 rules before insertion |
| `requirements.txt`  | Lists all required Python packages                             |

---

## Validation Rules

Every AI-generated row must pass all 7 checks before being shown to the user:

1. All 24 required columns are present
2. Category is one of: `origin_change`, `prepend`, `forged_as_path`, `typo`
3. IP prefix matches valid format (e.g. `192.168.1.0/24`)
4. Propagation is a float between 0.0 and 1.0
5. `is_moas` is either 0 or 1
6. `edit_distance` is an integer between 1 and 4
7. Title does not duplicate any existing entry in the dataset

Rows that fail any check are shown separately with the reason highlighted in red.

---

## Troubleshooting

| Problem                       | Solution                                                            |
| ----------------------------- | ------------------------------------------------------------------- |
| `streamlit` not recognised    | Use `venv\Scripts\python -m streamlit run app.py`                   |
| `No module named streamlit`   | Run `venv\Scripts\pip install streamlit pandas requests`            |
| App spins forever on Generate | Check Ollama is running at `http://localhost:11434`                 |
| 0 rows returned               | Try setting n to 3 first — the 1B model works best in small batches |
| Timeout error                 | Reduce the number of rows to generate, or restart Ollama            |

---

## How the AI Generation Works

1. The app samples 5 real rows from your uploaded CSV
2. These are embedded into a detailed prompt describing every column rule
3. The prompt is sent to LLaMA 3.2 running locally via Ollama
4. LLaMA returns a JSON array of new rows following the same patterns
5. Requests are split into batches of 3 rows for reliability
6. Each batch is retried if it fails until the target count is reached
7. Every returned row is validated before being shown to the user

---

## Dataset

The sample dataset used for development and testing is the **BGP Network Hijack Dataset** containing 70 rows and 24 columns describing BGP routing events across 4 attack categories: `origin_change`, `prepend`, `forged_as_path`, and `typo`.
