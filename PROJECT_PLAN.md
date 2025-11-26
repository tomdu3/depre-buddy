# **Depre Buddy: Sequential Triage Agent \- Development Plan**

## **Project Overview**

**Goal:** To build a robust, multi-agent system that provides structured, empathetic mental health triage (based on the PHQ-9 framework) and delivers grounded, real-time resources.  
**Technology Stack:**

* **Backend:** Python, FastAPI, Gemini API (for LLM and Tools), In-Memory State Management.  
* **Frontend:** HTML, JavaScript (Vanilla JS), Tailwind CSS.  
* **Agent Concepts:** Sequential Agents, A2A Protocol, Built-in Tools (Google Search), Sessions & Memory.

## **High-Level Architecture**

The application follows a standard client-server model, with the core logic residing in the FastAPI backend, structured as a sequential multi-agent pipeline. The key components are the client, the API gateway, and the three specialized agent handlers that communicate sequentially.

## **Stage 1: Foundation & Backend Setup (FastAPI Core)**

**Objective:** Establish the FastAPI server, implement core API communication functions (LLM and Search), and define the initial session state structure.

| Task | Description | Implementation Details | Deliverable |
| :---- | :---- | :---- | :---- |
| **1.1 Project Setup** | Initialize FastAPI and define basic dependencies. | Create main.py with FastAPI app initialization and necessary imports (e.g., requests, json, LLM helpers). | main.py with basic structure. |
| **1.2 LLM Helper Function** | Create a reusable function to call the Gemini API for standard text generation. | Implement gemini\_llm\_response(prompt, system\_instruction) using gemini-2.5-flash-preview-09-2025. | Function for text generation. |
| **1.3 Search Tool Function** | Create a reusable function to call the Gemini API with Google Search grounding enabled. | Implement gemini\_search\_tool(query) to enable the tools: \[{ "google\_search": {} }\] property. | Function for grounded search. |
| **1.4 Session Manager** | Define the global session store and state structure. | Use a dictionary (session\_store \= {}) to hold session data. Each session must include: history, step, phq9\_score, phq9\_data. | Global session\_store definition. |
| **1.5 Core API Endpoint** | Create the main /chat endpoint to handle all user-agent interactions. | Define the POST /chat endpoint that accepts session\_id and user\_message. This endpoint will use state\["step"\] to call the correct agent handler. | Functional /chat endpoint skeleton. |

## **Stage 2: Core Agent Logic & State Management**

**Objective:** Implement the three sequential agent handlers and the logic to manage control flow using the A2A protocol pattern.

| Task | Description | Implementation Details | Deliverable |
| :---- | :---- | :---- | :---- |
| **2.1 PHQ-9 Definition** | Define the content and structure of the PHQ-9 questions. | Store the 8 core questions and the severity rating scale (0-3) in a Python array/dictionary. | PHQ\_9\_QUESTIONS data structure. |
| **2.2 Triage Agent Handler** | Implement the first agent responsible for safety check and data collection. | TriageAgent\_handler: Handles the immediate crisis check (PHQ-9 Item 9\) and prompts the user through the 8 questions, saving responses to session\_store. | Functional TriageAgent\_handler. |
| **2.3 Assessment Agent Handler** | Implement the second agent responsible for calculating the PHQ-9 score and category. | AssessmentAgent\_handler: Calculates the total score and assigns the risk level (CRISIS, PROFESSIONAL, MONITORING, MINIMAL). **This handler uses the A2A pattern to switch control** by setting state\["step"\] \= "ResourceAgent\_Final". | Functional AssessmentAgent\_handler. |
| **2.4 Resource Agent Handler** | Implement the final agent responsible for empathetic response and resource lookup. | ResourceAgent\_handler: Uses the calculated risk level to define a system prompt (Context Engineering) and a search query. Calls gemini\_llm\_response and gemini\_search\_tool. | Functional ResourceAgent\_handler. |
| **2.5 A2A Control Logic** | Integrate the agent handlers within the /chat endpoint for sequential execution. | The /chat endpoint must dynamically call the function determined by session\_store\[session\_id\]\["step"\]. | Fully functional sequential agent pipeline. |

## **Stage 3: Frontend Development & Integration**

**Objective:** Create a responsive, intuitive chat interface and integrate it with the FastAPI backend.

| Task | Description | Implementation Details | Deliverable |
| :---- | :---- | :---- | :---- |
| **3.1 HTML/Tailwind Structure** | Define the layout for the single-page application. | Create index.html with a centered chat container, input field, and a message display area. Use Tailwind for mobile-first responsiveness and the "Calm Reliability" palette. | index.html structure and styling. |
| **3.2 Initial JS Setup** | Implement core frontend logic for session management. | Implement generateSessionId() function (using crypto.randomUUID()) and getOrCreateSession(). | JS functions for session handling. |
| **3.3 UI Rendering Logic** | Implement functions to dynamically display messages. | Implement renderMessage(sender, text) to display messages in the chat history. Handle markdown rendering for LLM responses. | UI rendering functions. |
| **3.4 API Communication** | Create the core frontend function to talk to the backend. | Implement sendMessage() to asynchronously fetch the FastAPI /chat endpoint, passing the session\_id and user\_message. Include a loading spinner. | sendMessage function integrated. |
| **3.5 First Interaction Test** | Verify end-to-end communication and state preservation. | Test the initial greeting and the first few Triage Agent prompts. | Functional Chat UI interacting with the Triage Agent. |

## **Stage 4: Testing, Refinement & Submission Prep**

**Objective:** Thoroughly test the application across all scenarios and finalize all documentation required for the Capstone submission.

| Task | Description | Implementation Details | Deliverable |
| :---- | :---- | :---- | :---- |
| **4.1 Scenario Testing** | Test all four possible final recommendation paths. | Test cases for: CRISIS (immediate risk), PROFESSIONAL (high score), MONITORING (low score, short duration), MINIMAL (very low score). | Verified functional agent pipeline. |
| **4.2 Error Handling** | Implement robust error handling in both backend and frontend. | Backend: Add try/except blocks to handle API failures. Frontend: Display user-friendly error messages if the API call fails. | Enhanced error resilience. |
| **4.3 Final Documentation** | Review and complete the Capstone writeup. | Ensure the provided depre\_buddy\_writeup.md is updated with specific A2A and implementation details, and that the architecture description is clear. | Finalized depre\_buddy\_writeup.md. |
| **4.4 Code Clean-up** | Add detailed comments and ensure no API keys are present in the code. | Review all functions for clarity and remove any hardcoded secrets. | Production-ready code (without secrets). |

