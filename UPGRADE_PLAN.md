# Depre-Buddy Improvements: Routing Fixes & Premium UI Implementation

This upgrade plan outlines the steps to resolve routing bugs, session state isolation issues, and crisis-checking safety gaps in the FastAPI/ADK backend, and to build a premium, highly interactive frontend chat interface.

## Proposed Changes

### Backend Core (`main.py` & API Endpoints)

---

#### [MODIFY] [main.py](file:///home/tom/projects/depre-buddy/main.py)
* **Agent Routing Fix**: Modify `route_to_agent()` to check if triage has been completed before moving to the assessment agent. Introduce a `triage_completed` state flag.
* **Session Isolation Fix**: Update all `run_debug` calls to pass the `session_id=session_id` parameter, preventing session history clashes across concurrent users.
* **Crisis Checking Safety Update**: Modify `update_session_state()` to run the crisis detection tool on *every* user message, rather than only when the active agent is `triage_agent`.
* **Static Files Mounting**: Import `StaticFiles` and serve a `static` directory. Route `/` to serve the HTML chat client. Update `/` path to `/api/health` for the JSON health status.

---

### Frontend UI Component

---

#### [NEW] [index.html](file:///home/tom/projects/depre-buddy/static/index.html)
* Create the HTML structure for the single-page application.
* Link to Google Fonts (Outfit and Inter) and the stylesheet.
* Include a responsive header with the app's status, active agent badge, and a progress tracker (e.g., question numbers and PHQ-9 scoring indicators).
* Create a dedicated section for quick-reply buttons (0 to 3) during the assessment phase.

#### [NEW] [style.css](file:///home/tom/projects/depre-buddy/static/style.css)
* Design a premium custom styling system:
  * **Color Palette**: Calming indigo, violet, slate-grey, and emergency red/amber.
  * **Glassmorphic Cards**: Semitransparent containers with subtle backdrop blur (`backdrop-filter`) and thin borders.
  * **Smooth Micro-animations**: Micro-transitions on hover states, keyframe-based message entrance slides, and a custom pulsing typing indicator.
  * **Custom Scrollbars**: Modern, thin, rounded scrollbars for the chat container.

#### [NEW] [app.js](file:///home/tom/projects/depre-buddy/static/app.js)
* Handle session lifecycle: request a session ID via `/session/new` on load, and store it in `localStorage`.
* Handle chat submissions: append messages to the DOM, show the custom typing indicator, and POST request data to `/chat`.
* Dynamically render markdown elements (bold text, lists, and line breaks) for natural formatting.
* Detect the current agent and score from API responses:
  * If the active agent is `assessment_agent`, display the PHQ-9 question number and show the quick-selection buttons (0: Not at all, 1: Several days, 2: More than half the days, 3: Nearly every day).
  * If the active agent is `resource_agent` or a crisis is flagged, display a structured emergency panel with urgent contact details.
  * Update the progress indicator dynamically.

---

## Verification Plan

### Automated Tests
* We will write automated pytest tests in [test_main.py](file:///home/tom/projects/depre-buddy/test_main.py) to verify:
  * The Triage Agent runs on the first turn and doesn't get skipped.
  * Session isolation works properly (submitting messages on two different session IDs isolates history).
  * Crisis detection works during both triage and assessment phases.
* Run tests with:
  ```bash
  uv run pytest test_main.py
  ```

### Manual Verification
* Start the local server:
  ```bash
  uv run uvicorn main:app --reload
  ```
* Open `http://localhost:8000` in the browser.
* Perform a full walkthrough:
  * Check the greeting and response from the Triage Agent.
  * Walk through the PHQ-9 questions using the quick-choice buttons and manual typing.
  * Verify the score, category classification, and Resource Agent transition.
  * Verify that a new session with crisis words ("I want to die") triggers the emergency hotline screen immediately.
