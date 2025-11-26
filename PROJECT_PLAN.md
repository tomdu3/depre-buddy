# **Depre Buddy: Sequential Triage Agent \- Development Plan**

## **Project Overview**

**Goal:** To build a robust, multi-agent system that provides structured, empathetic mental health triage (based on the PHQ-9 framework) and delivers grounded, real-time resources. The entire workflow simulates the **Sequential Agent** pattern and **Agent-to-Agent (A2A)** communication.  
**Constraint:** The entire system must be developed and run locally, avoiding all cloud deployment services (e.g., Cloud Run, Vertex AI) and relying only on standard Python libraries (FastAPI, Requests) and the public Gemini API endpoint.  
**Technology Stack:**

* **Backend:** Python, FastAPI, Gemini API (for LLM and Tools), In-Memory State Management (session\_store).  
* **Frontend:** HTML, JavaScript (Vanilla JS), Tailwind CSS (for aesthetics and mobile-first design).  
* **Agent Concepts:** Sequential Agents (Day 1b), A2A Protocol (Day 5a), Built-in Tools (Google Search Grounding, Day 2a/2b), Sessions & Memory (Day 3a).

## **High-Level Architecture**

The application uses a sequential, pipeline-style flow, where the current state\["step"\] determines which specialized agent handler is active. Control is explicitly passed via function calls, simulating the A2A handoff.

## **Stage 1: Foundation & Backend Setup (FastAPI Core)**

**Objective:** Establish the FastAPI server, implement core API communication functions (LLM and Search), and define the initial session state structure.

| Task | Description | Implementation Details | Deliverable |
| :---- | :---- | :---- | :---- |
| **1.1 Project Setup** | Initialize FastAPI and define basic dependencies. | Create main.py with FastAPI app initialization. Include call\_api\_with\_backoff utility to handle transient API errors, as practiced in the course. | main.py with basic structure and error utility. |
| **1.2 LLM Helper Function** | Create a reusable function to call the Gemini API for standard text generation. | Implement agent\_llm\_text\_generation(prompt, system\_instruction) using gemini-2.5-flash-preview-09-2025 with **no tools** enabled. Used primarily by the Triage Agent. | Function for text generation. |
| **1.3 Search Tool Function** | Create a reusable function to call the Gemini API with Google Search grounding enabled. | Implement gemini\_search\_tool(query, system\_instruction) which sets the tools: \[{ "google\_search": {} }\] property. **This simulates an external tool.** Used by the Resource Agent. | Function for grounded search. |
| **1.4 Session Manager** | Define the global session store and state structure. | Use a global Python dictionary (session\_store) for in-memory session state (Day 3a). Initial state must include: history, step (starts at TriageAgent\_Init), phq9\_score, phq9\_data. | Global session\_store definition. |
| **1.5 Core API Endpoint** | Create the main /chat endpoint to handle all user-agent interactions. | Define the POST /chat endpoint. It retrieves the current state and routes the request by calling the function mapped to state\["step"\] in the AGENT\_HANDLERS dictionary. | Functional /chat endpoint skeleton with dynamic routing. |

## **Stage 2: Core Agent Logic & State Management**

**Objective:** Implement the three sequential agent handlers and the logic to manage control flow using the A2A protocol pattern (Day 5a).

| Task | Description | Implementation Details | Deliverable |
| :---- | :---- | :---- | :---- |
| **2.1 PHQ-9 Definition & Tool** | Define the PHQ-9 content and implement the deterministic scoring tool. | Store the 8 core questions in a Python list (PHQ\_9\_QUESTIONS). Implement the **Function Tool** simulation: classify\_phq9\_score(score: int) which returns the severity string. | PHQ\_9\_QUESTIONS and classify\_phq9\_score function. |
| **2.2 Triage Agent Handler** | Implement the first agent responsible for safety check and data collection. | TriageAgent\_handler: Handles the initial crisis check (safety) and prompts the 8 questions sequentially. Upon completion of duration collection, it **performs A2A handoff** via return await AssessmentAgent\_handler(...). | Functional TriageAgent\_handler with sequential state updates and crisis override logic. |
| **2.3 Assessment Agent Handler** | Implement the second agent responsible for calculating the PHQ-9 score and category. | AssessmentAgent\_handler: Retrieves phq9\_score from state, calls the **Function Tool** (classify\_phq9\_score), and uses the **A2A pattern** to immediately call and switch control to the Resource Agent: return await ResourceAgent\_handler(...). | Functional AssessmentAgent\_handler using the deterministic tool and A2A handoff. |
| **2.4 Resource Agent Handler** | Implement the final agent responsible for empathetic response and resource lookup. | ResourceAgent\_handler: Uses the severity category to set the appropriate System Prompt (**Context Engineering**) and calls the **External Tool Simulation** (gemini\_search\_tool) to get grounded advice. | Functional ResourceAgent\_handler providing final grounded response and source citations. |
| **2.5 Observability Simulation** | Integrate simulated logging for tracing the sequential flow. | Add print() statements tagged with \[ADK Agent Handoff Log\] at the beginning and end of each agent handler to trace the execution path (Day 4a concept). | Logs confirming successful A2A transitions in the console. |

## **Stage 3: Frontend Development & Integration**

**Objective:** Create a responsive, intuitive chat interface and integrate it with the FastAPI backend using standard web technologies.

| Task | Description | Implementation Details | Deliverable |
| :---- | :---- | :---- | :---- |
| **3.1 HTML/Tailwind Structure** | Define the layout for the single-page application. | Create index.html with Tailwind CSS integration (using the CDN). The layout must be a clean, mobile-responsive chat box with rounded corners and clear contrast (**Aesthetics is crucial**). | index.html structure and styling. |
| **3.2 Initial JS Setup** | Implement core frontend logic for session management. | Implement generateSessionId() (using crypto.randomUUID()) and ensure the session ID is persisted in localStorage for the browser session. | JS functions for session handling. |
| **3.3 UI Rendering Logic** | Implement functions to dynamically display messages. | Implement renderMessage(sender, text) that handles dynamic HTML insertion. Use a library or custom logic to render simple Markdown (e.g., \*\*bold\*\*, \*italics\*) from the LLM responses. | UI rendering functions in Vanilla JS. |
| **3.4 API Communication** | Create the core frontend function to talk to the backend. | Implement sendMessage() to asynchronously fetch the /chat endpoint. Include client-side validation and a simple loading spinner/indicator to handle the latency of the LLM calls. | sendMessage function integrated with loading state. |
| **3.5 First Interaction Test** | Verify end-to-end communication and state preservation. | Test the initial greeting, the crisis check, and the first PHQ-9 question to ensure the session\_id is correctly maintained across requests. | Functional Chat UI interacting with the Triage Agent. |

## **Stage 4: Testing, Refinement & Submission Prep**

**Objective:** Thoroughly test the application across all scenarios and finalize all documentation required for the Capstone submission.

| Task | Description | Implementation Details | Deliverable |
| :---- | :---- | :---- | :---- |
| **4.1 Scenario Testing** | Test all four possible final recommendation paths. | Test cases for: CRISIS (triggering score 99), SEVERE (score $\\ge 20$), MODERATE (score $10-14$), MINIMAL (score $\\le 4$). Verify tool usage in the logs. | Verified functional agent pipeline. |
| **4.2 Error Handling** | Implement robust error handling in both backend and frontend. | Backend: Ensure the call\_api\_with\_backoff handles Gemini API failures gracefully. Frontend: Display a non-disruptive error message if the /chat endpoint fails. | Enhanced error resilience. |
| **4.3 Final Documentation** | Review and complete the Capstone writeup. | Ensure the provided depre\_buddy\_writeup.md is updated with specific references to the ADK course concepts used (e.g., "The direct function call from AssessmentAgent\_handler to ResourceAgent\_handler simulates the **A2A Protocol**"). | Finalized depre\_buddy\_writeup.md. |
| **4.4 Code Clean-up** | Add detailed comments and ensure no API keys are present in the code. | Review all functions for clarity and ensure API\_KEY \= "" is used. | Production-ready code (without secrets). |
