"""
main.py
Application entry point. Run: python main.py

Set OPENAI_API_KEY environment variable (or in .env) to use the live LLM.
Leave it unset to run in offline demo mode with the scripted mock.
"""

import os
import sys

# Allow running from project root
sys.path.insert(0, os.path.dirname(__file__))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional

from data.repositories import PatientRepository, SessionRepository, AlertRepository
from core.llm_client import OpenAIClient, MockLLMClient
from core.agent_controller import AgentController
from ui.main_app import MainApp


def build_llm():
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if api_key and api_key != "your_key_here":
        print("[INFO] Using OpenAI live client (GPT-4o)")
        try:
            return OpenAIClient(api_key=api_key, model="gpt-4o")
        except ImportError:
            print("[WARN] openai package not installed — falling back to mock client")
    print("[INFO] Using scripted mock LLM client (offline demo mode)")
    return MockLLMClient()


def main():
    # Repositories
    patient_repo = PatientRepository()
    session_repo = SessionRepository()
    alert_repo   = AlertRepository()

    # LLM + Agent
    llm = build_llm()
    agent = AgentController(
        llm=llm,
        patient_repo=patient_repo,
        session_repo=session_repo,
        alert_repo=alert_repo,
    )

    # Launch UI
    app = MainApp(
        patient_id="PATIENT_001",
        agent_controller=agent,
        patient_repo=patient_repo,
        alert_repo=alert_repo,
        auto_notify_ms=4000,
    )
    app.mainloop()


if __name__ == "__main__":
    main()
