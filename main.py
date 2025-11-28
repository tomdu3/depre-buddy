import os
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

# ADK imports
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import google_search
from google.genai import types

# Local tool imports
from tools.crisis_detection import CrisisDetectionTool
from tools.phq9_assessment import PHQ9AssessmentTool

# Config imports
from config import Settings


# --- Project Setup ---
settings = Settings()

# --- ADK Retry Configuration ---
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7, 
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504]
)

# --- ADK Session Store ---
session_store: Dict[str, Dict[str, Any]] = {}

# --- ADK Tools Initialization ---
crisis_tool = CrisisDetectionTool()
phq9_tool = PHQ9AssessmentTool()

# --- ADK Agents Definition ---

# Triage Agent - Handles initial crisis detection and routing
triage_agent = Agent(
    name="triage_agent",
    model=Gemini(
        model=settings.MODEL_NAME,
        retry_options=retry_config
    ),
    description="Mental health triage agent that detects crises and starts assessment",
    instruction="""You are a compassionate mental health triage specialist. 
    
YOUR RESPONSIBILITIES:
1. Greet users warmly and assess their immediate mental state
2. Use the crisis_detection tool if you suspect any crisis situation
3. Start the PHQ-9 assessment for non-crisis situations
4. Be empathetic, non-judgmental, and focused on user safety

CRISIS DETECTION:
- If the user mentions self-harm, suicide, or immediate danger, use crisis_detection immediately
- For crisis situations, provide emergency resources and support

PHQ-9 ASSESSMENT:
- For non-crisis situations, begin the PHQ-9 assessment using administer_question
- Start with question 1 and guide the user through the process

Always prioritize user safety and provide a supportive, understanding environment.""",
    tools=[crisis_tool.detect_crisis, phq9_tool.administer_question],
)

# Assessment Agent - Handles PHQ-9 assessment and scoring
assessment_agent = Agent(
    name="assessment_agent",
    model=Gemini(
        model=settings.MODEL_NAME,
        retry_options=retry_config
    ),
    description="Clinical assessment agent that administers PHQ-9 and provides scoring",
    instruction="""You are a clinical mental health assessment specialist. 

YOUR RESPONSIBILITIES:
1. Administer the PHQ-9 depression assessment professionally
2. Guide users through all 8 questions with empathy and clarity
3. Use the administer_question tool to process responses and track progress
4. Calculate scores and provide appropriate clinical context
5. Emphasize that this is a screening tool, not a diagnosis

ASSESSMENT PROCESS:
- Ask one question at a time using the administer_question tool
- Help users understand the scoring scale (0-3)
- Be supportive and understanding throughout the process
- When complete, provide the score and appropriate next steps

USER GUIDANCE:
- If the user provides a non-numerical answer, gently guide them to provide a score between 0 and 3. For example, you can say: "I understand you're feeling down. To help me understand better, could you please rate how much you've been bothered by this on a scale of 0 to 3, where 0 is 'Not at all' and 3 is 'Nearly every day'?"
- If the user's answer is vague, ask for clarification. For example, if they say "a little," you can ask: "On a scale of 0 to 3, what number would you say 'a little' corresponds to?"
- Continue the assessment until all 8 questions have been answered with a valid numerical score.
""",
    tools=[phq9_tool.administer_question, crisis_tool.detect_crisis],
)

# Resource Agent - Provides tailored mental health resources
resource_agent = Agent(
    name="resource_agent",
    model=Gemini(
        model=settings.MODEL_NAME,
        retry_options=retry_config
    ),
    description="Mental health resource specialist providing grounded, actionable resources",
    instruction="""You are a mental health resource specialist. 

YOUR RESPONSIBILITIES:
1. Provide appropriate mental health resources based on the user's situation
2. Use Google Search to find current, relevant information and local resources
3. Include crisis resources when needed
4. Offer practical next steps and emphasize that help is available
5. Provide hope and encouragement

RESOURCE GUIDELINES:
- For crisis situations: Provide immediate hotlines and emergency contacts
- For assessment results: Tailor resources to the severity level
- Always include: Therapy options, support groups, self-help strategies
- Provide specific, actionable steps the user can take
- Emphasize that professional help is available and effective""",
    tools=[google_search, crisis_tool.detect_crisis],
)

# --- Agent Runners ---
triage_runner = InMemoryRunner(agent=triage_agent)
assessment_runner = InMemoryRunner(agent=assessment_agent)
resource_runner = InMemoryRunner(agent=resource_agent)

# --- FastAPI App ---
app = FastAPI(
    title="Depre Buddy Sequential Triage Agent", version="2.0",
    description="A sequential triage agent for mental health assessment and resource provision"
    )

# --- Pydantic Models ---
class ChatRequest(BaseModel):
    session_id: str
    user_message: str

class SessionResponse(BaseModel):
    session_id: str
    message: str
    current_agent: str
    phq9_score: Optional[int] = None
    assessment_category: Optional[str] = None
    crisis_detected: Optional[bool] = None

# --- Session Management ---
def get_initial_session_state() -> Dict[str, Any]:
    """Create initial session state following ADK patterns"""
    return {
        "current_agent": "triage_agent",
        "history": [],
        "phq9_data": {},
        "phq9_score": 0,
        "phq9_current_question": 1,
        "assessment_category": None,
        "crisis_detected": False,
        "completed_assessment": False,
        "created_at": str(uuid.uuid4())
    }

def route_to_agent(state: Dict[str, Any], user_message: str) -> str:
    """ADK-style agent routing logic"""
    current_agent = state["current_agent"]
    
    # Crisis always goes to resource agent for emergency help
    if state.get("crisis_detected"):
        return "resource_agent"
    
    # Agent progression logic
    if current_agent == "triage_agent":
        # After triage, move to assessment if no crisis
        if not state.get("crisis_detected"):
            return "assessment_agent"
    
    elif current_agent == "assessment_agent":
        # After assessment completion, move to resources
        if state.get("completed_assessment"):
            return "resource_agent"
    
    # Default: stay with current agent
    return current_agent

async def update_session_state(state: Dict[str, Any], agent_type: str, user_message: str, response: Any):
    """Update session state based on agent interactions and tool usage"""
    
    # Update history
    state["history"].append({"role": "user", "text": user_message})
    state["history"].append({"role": "agent", "text": str(response)})
    
    # State updates based on agent type
    if agent_type == "triage_agent":
        # Check for crisis in user message
        crisis_check = await crisis_tool.detect_crisis(user_message)
        if crisis_check.get("crisis_detected"):
            state["crisis_detected"] = True
    
    elif agent_type == "assessment_agent":
        # Process PHQ-9 responses
        if user_message.strip().isdigit() and 0 <= int(user_message) <= 3:
            current_q = state["phq9_current_question"]
            score = int(user_message)
            state["phq9_data"][current_q] = score
            
            # Move to next question or complete assessment
            next_q = current_q + 1
            if next_q <= 8:
                state["phq9_current_question"] = next_q
            else:
                # Assessment complete
                state["completed_assessment"] = True
                state["phq9_score"] = sum(state["phq9_data"].values())
                state["assessment_category"] = phq9_tool.classify_score(state["phq9_score"])

# --- API Endpoints ---
@app.get("/")
async def health_check():
    return {
        "status": "healthy", 
        "message": "DepraBuddy ADK Therapy API is running",
        "version": "2.0",
        "framework": "Google ADK",
        "active_sessions": len(session_store)
    }


@app.get("/agents")
async def list_agents():
    """List available ADK agents"""
    return {
        "agents": [
            {
                "name": "triage_agent",
                "description": "Mental health triage and crisis detection",
                "tools": ["crisis_detection", "phq9_assessment"]
            },
            {
                "name": "assessment_agent", 
                "description": "PHQ-9 clinical assessment administration",
                "tools": ["phq9_assessment", "crisis_detection"]
            },
            {
                "name": "resource_agent",
                "description": "Mental health resource provision",
                "tools": ["google_search", "crisis_detection"]
            }
        ]
    }

@app.post("/session/new")
async def create_new_session() -> Dict[str, Any]:
    """Create a new ADK therapy session"""
    session_id = str(uuid.uuid4())
    session_store[session_id] = get_initial_session_state()
    
    return {
        "session_id": session_id,
        "message": "New ADK therapy session created",
        "initial_agent": "triage_agent",
        "status": "active"
    }

@app.get("/session/{session_id}")
async def get_session_status(session_id: str) -> Dict[str, Any]:
    """Get the current status of a therapy session"""
    if session_id not in session_store:
        raise HTTPException(status_code=404, detail="Session not found")
    
    state = session_store[session_id]
    return {
        "session_id": session_id,
        "current_agent": state["current_agent"],
        "phq9_score": state.get("phq9_score"),
        "phq9_current_question": state.get("phq9_current_question"),
        "assessment_category": state.get("assessment_category"),
        "crisis_detected": state.get("crisis_detected", False),
        "completed_assessment": state.get("completed_assessment", False),
        "history_length": len(state["history"])
    }

@app.delete("/session/{session_id}")
async def delete_session(session_id: str) -> Dict[str, str]:
    """Delete a therapy session"""
    if session_id in session_store:
        del session_store[session_id]
        return {"message": f"Session {session_id} deleted"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.get("/sessions")
async def list_sessions() -> Dict[str, Any]:
    """List all active sessions (for debugging)"""
    return {
        "active_sessions": len(session_store),
        "sessions": list(session_store.keys())
    }


@app.post("/chat", response_model=SessionResponse)
async def chat_endpoint(request: ChatRequest) -> SessionResponse:
    """
    Main chat endpoint using ADK agent patterns
    """
    session_id = request.session_id
    user_message = request.user_message

    # Get or create session
    if session_id not in session_store:
        session_store[session_id] = get_initial_session_state()
        print(f"[ADK] New session created: {session_id}")
    
    state = session_store[session_id]
    
    try:
        # Determine which agent should handle this message
        target_agent = route_to_agent(state, user_message)
        state["current_agent"] = target_agent
        
        # Route to appropriate ADK agent
        if target_agent == "triage_agent":
            response = await triage_runner.run_debug(user_message)
            
        elif target_agent == "assessment_agent":
            # Add PHQ-9 context for the assessment agent
            current_q = state["phq9_current_question"]
            contextual_message = f"PHQ-9 Question {current_q}: {user_message}"
            response = await assessment_runner.run_debug(contextual_message)
            
        elif target_agent == "resource_agent":
            # Add assessment context for personalized resources
            context_info = ""
            if state.get("assessment_category"):
                context_info = f" Assessment Category: {state['assessment_category']}. PHQ-9 Score: {state.get('phq9_score', 'N/A')}."
            if state.get("crisis_detected"):
                context_info += " CRISIS SITUATION - Provide emergency resources."
                
            contextual_message = f"{user_message}{context_info}"
            response = await resource_runner.run_debug(contextual_message)
        
        # Update session state based on the interaction
        await update_session_state(state, target_agent, user_message, response)
        
        return SessionResponse(
            session_id=session_id,
            message=str(response),
            current_agent=target_agent,
            phq9_score=state.get("phq9_score"),
            assessment_category=state.get("assessment_category"),
            crisis_detected=state.get("crisis_detected", False)
        )
        
    except Exception as e:
        error_msg = f"Agent processing error: {str(e)}"
        print(f"[ADK Error] {error_msg}")
        return SessionResponse(
            session_id=session_id,
            message="I apologize, but I'm having trouble processing your request. Please try again.",
            current_agent=state["current_agent"],
            crisis_detected=state.get("crisis_detected", False)
        )

