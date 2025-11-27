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
- When complete, provide the score and appropriate next steps""",
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
