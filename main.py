import os
import requests
import json
from fastapi import FastAPI, Request, HTTPException
from config import Settings
from pydantic import BaseModel
from typing import Dict, Any, List
import uuid
import time
import re

# --- Project Setup ---
settings = Settings()

API_KEY = settings.GOOGLE_API_KEY
MODEL_NAME = settings.MODEL_NAME
SECRET_KEY = settings.SECRET_KEY

# --- 1.4 ADK CONCEPT: Session Manager (Simulating Session State) ---
# This global dictionary stores all active session data in memory.
# In a real ADK system, this would be managed automatically or by a database.
session_store: Dict[str, Dict[str, Any]] = {}

def get_initial_session_state() -> Dict[str, Any]:
    """Defines the initial structure for a new session."""
    return {
        # The 'step' determines which Agent Handler function is active.
        "step": "TriageAgent_Init", 
        "history": [], 
        "phq9_data": {}, 
        "phq9_score": 0,  
        "phq9_current_item": 0,
        "duration": None,
        "assessment_category": None
    }

# --- 1.1 Project Setup: FastAPI Initialization ---
app = FastAPI(title="Depre Buddy Sequential Triage Agent", version="1.0")


# --- SHARED UTILITIES (Error Handling & API Communication) ---

def call_api_with_backoff(url: str, payload: Dict[str, Any], max_retries: int = 5) -> Dict[str, Any]:
    """
    Handles API calls with retries using exponential backoff.
    This is critical for production readiness to manage transient network errors.
    """
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload)
            response.raise_for_status() # Raises an exception for 4xx or 5xx errors
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"API call failed, retrying in {wait_time}s... Error: {e}")
                time.sleep(wait_time)
            else:
                # If all retries fail, raise an HTTPException
                raise HTTPException(status_code=500, detail=f"Gemini API failed after multiple retries: {e}")

# --- LLM Helper Function (Simulating Agent LLM Calls) ---
async def agent_llm_text_generation(prompt: str, system_instruction: str) -> str:
    """Simulates a core LLM Agent call for text generation without tools."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]},
    }
    
    try:
        result = call_api_with_backoff(url, payload)
        # Extract the text response
        return result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "Error: Could not generate response.")
    except HTTPException as e:
        print(f"Error in agent_llm_text_generation: {e.detail}")
        return f"System Error during LLM call: {e.detail}"

# --- External Tool Simulation (Google Search Grounding) ---
async def gemini_search_tool(query: str, system_instruction: str) -> Dict[str, Any]:
    """
    Simulates an ADK Tool that uses Google Search grounding. 
    This will be used by the Resource Agent for real-time, grounded advice.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"
    
    full_prompt = f"Based on your access to real-time information, respond to the user's need: {query}"
    
    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        # Enable Google Search grounding (Agent Tools)
        "tools": [{"google_search": {} }], 
    }
    
    try:
        result = call_api_with_backoff(url, payload)
    except HTTPException:
        # Return a simple error response structure
        return {"text": "System Error: Search Tool failed.", "sources": []}
        
    candidate = result.get("candidates", [{}])[0]
    text = candidate.get("content", {}).get("parts", [{}])[0].get("text", "Error: Could not retrieve resource information.")
    
    # Extract Grounding Sources/Citations (Essential for a grounded tool)
    sources = []
    grounding_metadata = candidate.get("groundingMetadata")
    if grounding_metadata and grounding_metadata.get("groundingAttributions"):
        sources = [
            {"uri": attr.get("web", {}).get("uri"), "title": attr.get("web", {}).get("title")}
            for attr in grounding_metadata["groundingAttributions"]
        ]
        
    return {"text": text, "sources": sources}

# --- PHQ-9 DEFINITION & FUNCTION TOOL SIMULATION ---

# The 8 core questions of the PHQ-9 (scores 0-3) --> https://www.mdcalc.com/calc/1725/phq9-patient-health-questionnaire9
PHQ_9_QUESTIONS = {
    1: "Little interest or pleasure in doing things?",
    2: "Feeling down, depressed, or hopeless?",
    3: "Trouble falling or staying asleep, or sleeping too much?",
    4: "Feeling tired or having little energy?",
    5: "Poor appetite or overeating?",
    6: "Feeling bad about yourself—or that you are a failure or have let yourself or your family down?",
    7: "Trouble concentrating on things, such as reading the newspaper or watching television?",
    8: "Moving or speaking so slowly that other people could have noticed? Or the opposite—being so fidgety or restless that you have been moving around a lot more than usual?",
}

# The deterministic tool logic (Function Tool)
def classify_phq9_score(score: int) -> str:
    """Calculates the severity category from the total PHQ-9 score."""
    if score >= 20:
        return "CRISIS_SEVERE" # Severe (Need immediate professional attention)
    elif score >= 15:
        return "PROFESSIONAL_MODERATE_HIGH" # Moderately Severe (Need intervention)
    elif score >= 10:
        return "MONITORING_MILD_MODERATE" # Mild to Moderate (Monitor, suggest professional help)
    elif score >= 5:
        return "MONITORING_MILD" # Mild (Monitor, suggest self-help)
    else:
        return "MINIMAL" # Minimal (No depression indicated)

# --- PLACEHOLDERS FOR AGENT HANDLERS ---

# We will define the actual agent logic later.
# For now, we need to define the function signature so the AGENT_HANDLERS map can use them.
async def TriageAgent_handler(session_id: str, user_message: str) -> Dict[str, str]:
    # Placeholder: The actual logic goes here later.
    state = session_store[session_id]
    
    if state["step"] == "TriageAgent_Init":
        # Simulate the first agent call to start the sequence
        system_prompt = "Act as an empathetic mental health triage agent. Greet the user and ask the immediate crisis question."
        agent_response = await agent_llm_text_generation(
            prompt="The user is reaching out for support. Begin the conversation now.",
            system_instruction=system_prompt
        )
        state["step"] = "TriageAgent_Item9_Response"
        state["history"].append({"role": "user", "text": user_message})
        state["history"].append({"role": "agent", "text": agent_response})
        return {"message": agent_response}
    
    return {"message": f"Triage Agent is active. Current state: {state['step']}. (To be fully implemented later.)"}

# Define placeholders for the other agents
async def AssessmentAgent_handler(session_id: str, user_message: str = "") -> Dict[str, str]:
    return {"message": "Assessment Agent received control. (To be fully implemented later.)"}

async def ResourceAgent_handler(session_id: str, assessment_category: str) -> Dict[str, str]:
    return {"message": "Resource Agent received control. (To be fully implemented later.)"}


# --- ADK CONCEPT: Agent Handler Mapping & A2A Routing ---
# This dictionary is the central routing table for the Sequential Agent pattern.
AGENT_HANDLERS = {
    "TriageAgent_Init": TriageAgent_handler,
    "TriageAgent_Item9_Response": TriageAgent_handler,
    "TriageAgent_PHQ_Questions": TriageAgent_handler,
    "TriageAgent_Duration_Question": TriageAgent_handler,
    "AssessmentAgent_Score": AssessmentAgent_handler,
    "ResourceAgent_Final": ResourceAgent_handler,
    "Session_Complete": ResourceAgent_handler
}


# --- Core API Endpoint (Agent Runner) ---
class ChatRequest(BaseModel):
    session_id: str
    user_message: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest) -> Dict[str, str]:
    """
    Main entry point for all user interactions. 
    This function acts as the Agent Runner, determining the active agent 
    based on the session state (state["step"]).
    """
    session_id = request.session_id
    user_message = request.user_message

    # 1. Get or create the session state (Session Management)
    if session_id not in session_store:
        session_store[session_id] = get_initial_session_state()
        print(f"[ADK Session Log] New session created: {session_id}")
    
    state = session_store[session_id]
    
    # 2. Determine the current agent handler based on the state["step"]
    current_step = state["step"]
    handler = AGENT_HANDLERS.get(current_step)
    
    if not handler:
        error_message = f"Error: No agent handler found for step: {current_step}"
        print(f"[ADK Error Log] {error_message}")
        # Return a simple system error message to the client
        return {"message": f"System Error: Cannot find handler for step {current_step}. Please restart the session."}

    # 3. Call the appropriate agent handler (This is where the agent logic runs)
    try:
        # In this first stage, we call the TriageAgent_handler which initiates the chat flow.
        response = await handler(session_id, user_message) 
        return response
    except Exception as e:
        error_message = f"An unexpected error occurred during agent processing: {e}"
        print(f"[ADK Error Log] {error_message}")
        return {"message": f"An unexpected system error occurred: {str(e)}"}

# Health check endpoint
@app.get("/")
async def health_check():
    return {"status": "ok", "message": "Depre Buddy API is running."}