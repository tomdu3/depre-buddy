# Depre-Buddy

Depre-Buddy is an AI-powered mental health assistant designed to provide initial support for individuals who may be experiencing symptoms of depression. It uses a conversational AI agent to guide users through a preliminary assessment, detect potential crises, and offer appropriate resources.

## Main Features

- **Crisis Detection:** The assistant is trained to recognize language indicating a crisis (e.g., self-harm, suicidal ideation) and immediately provide emergency contact information and support hotlines.
- **PHQ-9 Assessment:** It administers the standard PHQ-9 (Patient Health Questionnaire-9) depression screening tool in a conversational format to assess the severity of depressive symptoms.
- **Sequential Agent Triage:** The system uses a multi-agent approach:
    1.  **Triage Agent:** The first point of contact, responsible for greeting the user and performing an initial crisis check.
    2.  **Assessment Agent:** If no crisis is detected, this agent takes over to administer the PHQ-9 assessment.
    3.  **Resource Agent:** Based on the assessment score, this agent provides tailored resources, such as information on different levels of depression, links to self-help materials, and suggestions for seeking professional help.
- **RESTful API:** The entire service is exposed via a FastAPI application, allowing for easy integration with web or mobile frontends.

## Stack and Libraries

- **Backend Framework:** FastAPI
- **AI Agent Framework:** Google Agent Development Kit (ADK)
- **Language Model:** Google Gemini (specifically `gemini-2.5-flash` by default)
- **Configuration:** Pydantic and `python-dotenv` for managing environment variables.
- **Core Libraries:**
    - `uvicorn` for serving the application.
    - `pytest` and `pytest-asyncio` for testing.

## Local Deployment

To run Depre-Buddy on your local machine, follow these steps:

1.  **Clone the Repository:**
    ```bash
    git clone <repository-url>
    cd depre-buddy
    ```

2.  **Set up a Python Environment:**
    This project uses `uv` to manage the virtual environment and dependencies.
    ```bash
    uv venv
    source .venv/bin/activate
    ```

3.  **Install Dependencies:**
    Synchronize your environment with the project's locked dependencies.
    ```bash
    uv sync
    ```

4.  **Set up Environment Variables:**
    Create a file named `.env` in the root of the project and add your Google API key:
    ```
    GOOGLE_API_KEY="your_google_api_key_here"
    ```
    You can also set an optional `SECRET_KEY` for the application.
    
    You can find an example of the `.env` file in the `env-sample` file. Copy it to `.env` and fill in your Google API key and secret key.

    ```bash
    cp env-sample .env
    ```

5.  **Run the Application:**
    ```bash
    uv run uvicorn main:app --reload
    ```
    The application will be available at `http://127.0.0.1:8000`.

6.  **API Documentation:**
    Once the server is running, you can access the interactive API documentation (provided by Swagger UI) at `http://127.0.0.1:8000/docs`.

## Trying it out

You can try it out by sending a POST request to `http://127.0.0.1:8000/new`. The response will contain a session ID.

{
  "session_id": "session_id_string",
  "message": "New ADK therapy session created",
  "initial_agent": "triage_agent",
  "status": "active"
}

Then you can send a POST request to `http://127.0.0.1:8000/chat` with the following body:

```json
{
  "session_id": "session_id_string",
  "user_message": "Message from the user.."
}
```

The response will contain the agent's response.

```json
{
  "session_id": "session_id_string",
  "message": "It's good that you're looking for things you can do....",
  "current_agent": "assessment_agent",
  "phq9_score": 0,
  "assessment_category": null,
  "crisis_detected": false
}
```

You can continue the conversation by sending another POST request to the same endpoint with the session ID and a new user message. The ai agent will respond based on the current state of the session, and the phq9 score questionnaire will be initiated, if the user would express feelings of depression. If the user would express feelings of crisis (expressions like `I want to kill myself`, or `I want to die`), the ai agent will immediately provide emergency contact information and support hotlines.


For more information on the API, see the [API Documentation](http://127.0.0.1:8000/docs). 