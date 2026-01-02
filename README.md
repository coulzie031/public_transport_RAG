

# 🗼 Paris Metro AI Agent (RAG + Tool Calling)

A containerized AI Assistant for Paris Public Transport. This application uses a Large Language Model (**Llama 3.1 405B**) equipped with real-time tools to plan itineraries, check traffic disruptions, and resolve station locations.

The project is built with **Python**, **Gradio**, and **Docker**, and integrates into a larger data pipeline involving **Kafka** and **Elasticsearch**.

---

## 🚀 Features

* **🧠 Intelligent Reasoning:** The agent doesn't just guess; it plans. It explains its thought process before executing actions (e.g., *"I need to find the ID for Gare de Lyon first"*).
* **🗺️ Itinerary Planning:** Calculates the best route between any two stations in Île-de-France.
* **⚠️ Disruption Alerts:** Checks real-time traffic updates for lines and stations.
* **📍 Fuzzy Station Matching:** Understands approximate names (e.g., "defense"  "La Défense").
* **💬 Streamed Responses:** See the agent's "thoughts" and tool outputs in real-time via the Web UI.

---

## 🏗️ Architecture

The system runs completely inside **Docker**.

### 1. The Agent Service (`paris-agent`)

* **Interface:** Gradio Web UI (Accessible at `http://localhost:7860`).
* **Brain:** Llama 3.1 405B (via NVIDIA API).
* **Logic:** A custom `while` loop that handles:
1. **User Query**  **LLM Reasoning**
2. **Tool Selection** (Traffic, Itinerary, Station Search)
3. **Execution** (Python functions calling IDFM APIs)
4. **Final Response**



### 2. The Data Pipeline (Background Services)

The agent sits on top of a robust data infrastructure defined in `docker-compose.yml`:

* **Kafka (KRaft Mode):** Handles real-time streams of transport data.
    - Manual update of the stations List (as stations rarly change)
    - Dynamic update of traffic infos (every 5 minutes) 
* **Elasticsearch:** Stores indexed station and alert data for fast retrieval (either with search or with embbeddings)
* **Producers & Sinks:** Python scripts that fetch data from the API and move it between Kafka and Elasticsearch.

--- 


## 🛠️ Prerequisites

* **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** (includes Docker Compose) installed and running.
* **[NVIDIA NIM API Key](https://build.nvidia.com/explore/discover)** (create an account to access Llama 3.1 405B and get API key).
* **[Île-de-France Mobilités (PRIM) API Key](https://prim.iledefrance-mobilites.fr/)** (register for a free account to access real-time transport data).
## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd public_transport_RAG

```

### 2. Configure Environment Variables

Create a `.env` file in the root directory. This keeps your keys secure.

```ini
# .env file
NVIDIA_API_KEY=nvapi-your-key-here
PRIM_TOKEN=your-prim-idfm-token-here

```

### 3. Build and Run

This command builds the Docker images and starts all core services (Agent, Kafka, Elasticsearch, sinks, etc.).

```bash
docker-compose up -d --build
```
The data ingestion producers are intentionally not started automatically in order to limit unnecessary calls to external APIs. They must be launched manually once to initialize the data.

```bash
docker-compose --profile manual run --rm station-producer
docker-compose --profile manual run --rm alert-producer
```

### 4. Access the App

Open your browser and go to:
👉 **[http://localhost:7860](https://www.google.com/search?q=http://localhost:7860)**

---

## 🖥️ How to Use

1. **Type a request:**
> *"I want to go from Gare de Lyon to La Defense"*


2. **Watch the thought process:**
* The agent will display `🧠 Reflection` explaining its plan.
* It will trigger `🛠️ Tool Request: get_station_id` to find exact coordinates.
* It will trigger `get_itinerary` with those IDs.


3. **Get the Result:** The final answer will summarize the best route.

**Note on Sessions:**
The chat memory is **per-browser-tab**. If you refresh the page, the conversation history is wiped. The agent currently does not store long-term memory in a database.

---

## 📂 Project Structure

```text
.
├── agent.py            # Main application logic (Gradio + LLM Loop)
├── docker-compose.yml       # Orchestration of all services
├── Dockerfile               # Environment definition for the Agent
├── requirements.txt         # Python dependencies
├── .env                     # API Keys (Not committed to Git)
├── tools/
│   └── tools.py         # Python functions wrapping the APIs
├── scripts/                    # Data Pipeline scripts
│   ├── station_producer.py     # Fetches stations data -> Kafka
│   ├── disturbance_producer.py # Fetches traffic data -> Kafka
│   ├── disturbance_sink.py     # Kafka-> embeddings-> Elasticsearch
│   └── stations_sink.py        # Kafka -> Elasticsearch
└── README.md

```

---

## 🔧 Troubleshooting

**1. "400 Bad Request" / API Errors**

* Ensure your `agent.py` includes the `sanitize_content` function. OpenAI/NVIDIA APIs require strings, not Gradio dictionaries.

**2. Network or Connection Refused**

* Check if containers are running: `docker compose ps`
* View logs: `docker compose logs -f paris-agent`

**3. "Unauthorized" Tool Calls**

* Verify that `PRIM_TOKEN` is correctly mapped in `docker-compose.yml` under the `paris-agent` service environment variables.
