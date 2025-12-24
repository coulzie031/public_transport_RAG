import os
import json
import gradio as gr
from openai import OpenAI
from tools.tools import get_disruption_context, get_station_id, get_itinerary

# --- 1. CONFIGURATION ---
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ.get("NVIDIA_API_KEY")
)
MODEL_ID = "meta/llama-3.1-405b-instruct"

# --- 2. DEFINE TOOLS ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_disruption_context",
            "description": "Get real-time Paris Metro traffic updates.",
            "parameters": {"type": "object", "properties": {"user_query": {"type": "string"}}, "required": ["user_query"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_station_id",
            "description": "Resolves a fuzzy station name to its exact API ID.",
            "parameters": {"type": "object", "properties": {"station_name": {"type": "string"}}, "required": ["station_name"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_itinerary",
            "description": "Calculates the best route between two stations.",
            "parameters": {
                "type": "object", 
                "properties": {"start_station": {"type": "string"}, "end_station": {"type": "string"}}, 
                "required": ["start_station", "end_station"]
            }
        }
    }
]

# --- 3. HELPER: CONTENT SANITIZER (Required for API Stability) ---
def sanitize_content(content):
    """
    Forces content to be a simple string.
    Fixes the '400 Bad Request' error by flattening Gradio's list format.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join([
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        ])
    return str(content) if content else ""

# --- 4. CORE LOGIC (Adapted strictly from your run_agent) ---
def predict(message, history):
    # A. Build Conversation History
    # Using the EXACT system prompt from your working script
    messages = [
        {
            "role": "system", 
            "content": "You are a helpful public transport assistant. ALWAYS keep the same name for the transport means (Metro 1 is different from Line 1)"
        }
    ]
    
    # Add History (Sanitized)
    for entry in history:
        if isinstance(entry, list) or isinstance(entry, tuple):
            # Old Format
            messages.append({"role": "user", "content": sanitize_content(entry[0])})
            messages.append({"role": "assistant", "content": sanitize_content(entry[1])})
        elif isinstance(entry, dict):
            # New Format
            clean_content = sanitize_content(entry.get("content"))
            messages.append({"role": entry.get("role"), "content": clean_content})

    # Add current message
    messages.append({"role": "user", "content": sanitize_content(message)})

    full_log = "" 
    
    # B. The Agent Loop (Your Logic)
    while True:
        # 1. Ask the Model
        response = client.chat.completions.create(
            model=MODEL_ID, messages=messages, tools=tools, tool_choice="auto"
        )
        msg = response.choices[0].message
        
        # 2. Display Reasoning (The "Think" block)
        if msg.content:
            full_log += f"\n{msg.content}\n"
            yield full_log # Show progress to user

        # 3. CHECK: Is the model finished? (No tool calls)
        if not msg.tool_calls:
            # Loop ends here naturally
            break
        
        # 4. If tools ARE called, execute them
        messages.append(msg) # Add request to history
        
        for tool_call in msg.tool_calls:
            fn_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            # Show tool usage in UI
            full_log += f"\n🛠️ **Tool Request:** `{fn_name}`\n"
            yield full_log
            
            # Execute Python Code
            try:
                if fn_name == "get_disruption_context":
                    tool_result = get_disruption_context(args.get("user_query"))
                elif fn_name == "get_station_id":
                    tool_result = get_station_id(args.get("station_name"))
                elif fn_name == "get_itinerary":
                    tool_result = get_itinerary(args.get("start_station"), args.get("end_station"))
                else:
                    tool_result = f"Error: Tool '{fn_name}' not found."
            except Exception as e:
                tool_result = f"Error executing {fn_name}: {e}"

            # Add Result to History
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": fn_name,
                "content": str(tool_result),
            })
            
            full_log += f"✅ **Result:** Received.\n"
            yield full_log

# --- 5. LAUNCH UI ---
demo = gr.ChatInterface(
    fn=predict,
    title="🗼 Paris Metro AI Agent",
    description="Ask for routes, traffic updates, or station info.",
    examples=["Gare de Lyon to La Defense", "Traffic line 14"],
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
