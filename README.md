# 🚇 Project Logic: Real-Time Transit RAG

## 🎯 The Objective
The goal of this project is to build an AI assistant capable of answering questions about the Paris public transport network (RER, Metro, Tram) based on **live reality**, rather than static schedules. The system is designed to capture incidents the moment they occur and use that real-time context to generate accurate, up-to-the-minute responses.

---

## 🧠 System Logic & Architecture

The solution relies on a continuous data pipeline divided into three distinct logical phases: **Ingestion**, **Storage (with Time-Awareness)**, and **Generation**.

### Phase 1: The "Pulse" (Data Ingestion)
Since transit incidents occur unexpectedly, we cannot rely on a one-time data dump. We need a system with a heartbeat.

* **The Source:** We target the **PRIM API** (specifically the "Line Reports" or traffic alerts endpoint).
* **The Polling Logic:** A dedicated background process wakes up **every 5 seconds**. It checks the API for the current state of the entire network.
* **The Hand-off:** Instead of processing this massive amount of data immediately, the poller acts simply as a courier. It formats the alerts into discrete messages and pushes them into a streaming buffer (**Apache Kafka**). This decoupled approach ensures that data collection never stops, even if the downstream AI processing experiences latency.

### Phase 2: The "Short-Term Memory" (Vector Storage)
This is the most critical logic step. While a standard database is designed to remember data forever, for traffic updates, **old data is bad data**.

* **Consumption:** A listener process picks up the messages from the Kafka stream.
* **Vectorization:** It converts the raw text of the alert (e.g., *"Colis suspect à Châtelet"*) into mathematical vectors, allowing the AI to understand the *semantic meaning* of the incident.
* **Temporal Tagging:** As the vector is saved into the database, we attach a **Timestamp Tag**. This metadata effectively stamps every piece of data with an expiration date, which is essential for the retrieval phase.

### Phase 3: The "Brain" (Retrieval & Answer)
When a user asks a question like *"Is the RER B running smoothly?"*, the following logic sequence is triggered:

1.  **Time-Filtered Search:** The system searches the Vector Database for information relevant to "RER B." However, it applies a **Strict Time Filter**: it explicitly ignores any data older than **5 to 10 minutes**.
    * *Logic:* This ensures the AI only sees what is happening *now*, preventing it from "hallucinating" delays that happened yesterday.
2.  **Context Assembly:** The system gathers the raw data logs found within that specific 5-minute window.
3.  **LLM Synthesis:** We feed the retrieved context to the Large Language Model (LLM) with a specific instruction:
    > *"Here is the raw data from the last 5 minutes. Please parse it and answer the user's question in plain language."*
4.  **Response:** The LLM translates the technical logs into a helpful, human-readable answer.

---

## 🔄 Summary of Data Flow

1.  **Poller** grabs data from the API (every 5 seconds).
2.  **Kafka** buffers the stream to handle high throughput.
3.  **Vector DB** stores the data, tagging it with the exact time of arrival.
4.  **User Query** triggers a database search (filtered by `Time = Now`).
5.  **LLM** interprets the results and explains the situation to the user.