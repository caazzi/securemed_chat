import reflex as rx
import httpx
import json
import asyncio
from typing import List, Dict

import os
# Detect production environment or fallback to local
API_BASE_URL = os.environ.get("API_BASE_URL", "https://securemed-api-540951606920.southamerica-east1.run.app/api")
API_KEY = os.environ.get("SECUREMED_API_KEY", "dev_key_123")

class State(rx.State):
    """The app state."""
    
    # --- Demographics & Init ---
    age: int = 35
    gender: str = "Female"
    lang: str = "en"
    session_id: str = ""
    
    # --- Conversation Content ---
    chief_complaint: str = ""
    initial_answers: str = ""
    follow_up_answers: str = ""
    
    # --- UI State ---
    step: int = 0  # 0: Demographics, 1: Initial Qs, 2: Follow-up Qs, 3: Final
    loading: bool = False
    
    # Streaming content
    initial_questions_text: str = ""
    follow_up_questions_text: str = ""

    def change_age(self, val: str):
        """Handle string to int conversion for the age input."""
        try:
            self.age = int(val) if val else 0
        except ValueError:
            pass

    def set_gender(self, val: str):
        self.gender = val

    def set_lang(self, val: str):
        self.lang = val

    def set_chief_complaint(self, val: str):
        self.chief_complaint = val

    def set_initial_answers(self, val: str):
        self.initial_answers = val

    def set_follow_up_answers(self, val: str):
        self.follow_up_answers = val

    async def init_session(self):
        """Step 0 -> Step 1: Initialize Redis session."""
        if not self.chief_complaint:
            yield rx.window_alert("Please enter a chief complaint.")
            return
            
        self.loading = True
        yield
        
        async with httpx.AsyncClient() as client:
            try:
                # 1. Init Session
                resp = await client.post(
                    f"{API_BASE_URL}/session/init",
                    json={"age": self.age, "gender": self.gender, "lang": self.lang},
                    headers={"X-API-KEY": API_KEY},
                    timeout=10.0
                )
                if resp.status_code == 200:
                    self.session_id = resp.json().get("session_id")
                    self.step = 1
                    # Auto-trigger first questions
                    async for item in self.get_initial_questions():
                        yield item
                else:
                    yield rx.window_alert(f"Failed to init session: {resp.text}")
            except Exception as e:
                yield rx.window_alert(f"Error: {str(e)}")
            finally:
                self.loading = False

    async def get_initial_questions(self):
        """Step 1 Streaming: Trigger OPQRST questions."""
        self.loading = True
        self.initial_questions_text = ""
        yield
        
        async with httpx.AsyncClient() as client:
            try:
                headers = {"X-API-KEY": API_KEY}
                payload = {
                    "session_id": self.session_id,
                    "chief_complaint": self.chief_complaint
                }
                
                async with client.stream(
                    "POST", 
                    f"{API_BASE_URL}/initial-questions-stream", 
                    json=payload, 
                    headers=headers,
                    timeout=60.0
                ) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            chunk = json.loads(line[len("data: "):])
                            self.initial_questions_text += chunk
                            yield
            except Exception as e:
                yield rx.window_alert(f"Streaming Error: {str(e)}")
            finally:
                self.loading = False

    async def submit_initial_answers(self):
        """Step 1 -> Step 2: Push answers and trigger follow-up."""
        if not self.initial_answers:
            yield rx.window_alert("Please answer the questions.")
            return
            
        self.step = 2
        async for item in self.get_follow_up_questions():
            yield item

    async def get_follow_up_questions(self):
        """Step 2 Streaming: Trigger SAMPLE questions."""
        self.loading = True
        self.follow_up_questions_text = ""
        yield
        
        async with httpx.AsyncClient() as client:
            try:
                headers = {"X-API-KEY": API_KEY}
                payload = {
                    "session_id": self.session_id,
                    "initial_answers": self.initial_answers
                }
                
                async with client.stream(
                    "POST", 
                    f"{API_BASE_URL}/follow-up-questions-stream", 
                    json=payload, 
                    headers=headers,
                    timeout=60.0
                ) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            chunk = json.loads(line[len("data: "):])
                            self.follow_up_questions_text += chunk
                            yield
            except Exception as e:
                yield rx.window_alert(f"Streaming Error: {str(e)}")
            finally:
                self.loading = False

    async def submit_follow_up_answers(self):
        """Step 2 -> Step 3: Finalize."""
        if not self.follow_up_answers:
            yield rx.window_alert("Please answer the follow-up questions.")
            return
        self.step = 3

    async def download_report(self):
        """Step 3: Securely fetch PDF with API Key and trigger download."""
        self.loading = True
        yield
        
        async with httpx.AsyncClient() as client:
            try:
                headers = {"X-API-KEY": API_KEY}
                payload = {
                    "session_id": self.session_id,
                    "follow_up_answers": self.follow_up_answers
                }
                resp = await client.post(
                    f"{API_BASE_URL}/summarize-and-generate-pdf",
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                if resp.status_code == 200:
                    yield rx.download(
                        data=resp.content,
                        filename="SecureMed_Report.pdf"
                    )
                else:
                    yield rx.window_alert(f"Download failed: {resp.text}")
            except Exception as e:
                yield rx.window_alert(f"Download Error: {str(e)}")
            finally:
                self.loading = False
