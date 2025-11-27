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

# Config imports
from config import Settings


# --- Project Setup ---
settings = Settings()

API_KEY = settings.GOOGLE_API_KEY
MODEL_NAME = settings.MODEL_NAME
SECRET_KEY = settings.SECRET_KEY

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