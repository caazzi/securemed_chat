import reflex as rx
import httpx
import json
from typing import List, Dict

import os
from .i18n import translations

API_BASE_URL = os.environ.get("API_BASE_URL", "https://securemed-api-540951606920.southamerica-east1.run.app/api")
API_KEY = os.environ.get("SECUREMED_API_KEY", "")

class State(rx.State):
    """The app state."""

    @rx.var
    def t(self) -> dict:
        return translations.get(self.lang, translations["en"])

    @property
    def _t(self) -> dict:
        return translations.get(self.lang, translations["en"])

    @rx.var
    def gender_opts(self) -> List[str]:
        return self._t["gender_opts"]
        
    @rx.var
    def lang_opts(self) -> List[str]:
        return self._t["lang_opts"]

    @rx.var
    def step_names(self) -> List[str]:
        return self._t.get("step_names", [])
    
    # --- General Form State ---
    gender: str = "Female"
    lang: str = "en"
    session_id: str = ""
    
    # --- Step 2: Chief Complaint ---
    specialist: str = ""
    age_bracket: str = "26-35"
    chief_complaint: str = ""
    duration: str = ""
    complaint_detail: str = ""

    # --- Step 3: Medical History ---
    conditions: List[str] = []
    medications: List[str] = []
    allergies_flag: bool = False
    allergies_text: str = ""

    # --- Step 4: Lifestyle ---
    family_history: List[str] = []
    smoking: str = ""
    alcohol: str = ""

    # --- Conversation Content ---
    questions: List[str] = []
    current_answers: List[str] = []
    _qs_buffer: str = ""
    summary_text: str = ""
    
    # --- UI State ---
    step: int = 0  # 0: Demographics, 1-4: Form, 5: Q&A, 6: Summary
    loading: bool = False

    def detect_lang(self):
        """Infer language from browser headers."""
        try:
            accept_lang = self.router.headers.get("accept-language", "")
            if "pt" in accept_lang.lower().split(",")[0]:
                self.lang = "pt"
            else:
                self.lang = "en"
        except Exception:
            self.lang = "en"

    def set_gender(self, val: str):
        self.gender = val

    def set_lang(self, val: str):
        self.lang = val

    def set_chief_complaint(self, val: str):
        self.chief_complaint = val

    def set_age_bracket(self, val: str):
        self.age_bracket = val

    def set_duration(self, val: str):
        self.duration = val

    def set_specialist(self, val: str):
        self.specialist = val

    def set_complaint_detail(self, val: str):
        self.complaint_detail = val

    def toggle_condition(self, condition: str):
        if condition in self.conditions:
            self.conditions.remove(condition)
        else:
            self.conditions.append(condition)

    def toggle_family_history(self, item: str):
        if item in self.family_history:
            self.family_history.remove(item)
        else:
            self.family_history.append(item)

    def add_medication(self):
        self.medications.append("")

    def update_medication(self, idx: int, val: str):
        self.medications[idx] = val

    def remove_medication(self, idx: int):
        self.medications.pop(idx)

    def set_allergies_flag(self, val: bool):
        self.allergies_flag = val

    def set_allergies_text(self, val: str):
        self.allergies_text = val

    def set_smoking(self, val: str):
        self.smoking = val

    def set_alcohol(self, val: str):
        self.alcohol = val

    def set_answer(self, idx: int, val: str):
        answers = self.current_answers.copy()
        answers[idx] = val
        self.current_answers = answers

    def go_to_step_1(self):
        self.step = 1

    def go_to_step_2(self):
        self.step = 2

    def go_to_step_3(self):
        self.step = 3

    def go_to_step_4(self):
        self.step = 4

    async def init_session(self):
        """Step 4 -> Step 5: Initialize Redis session."""
        self.loading = True
        yield
        
        async with httpx.AsyncClient() as client:
            try:
                # payload conforming to Sprint 1
                payload = {
                    "age_bracket": self.age_bracket,
                    "sex": self.gender,
                    "lang": self.lang,
                    "specialist": self.specialist,
                    "chief_complaint": self.chief_complaint,
                    "duration": self.duration,
                    "complaint_detail": self.complaint_detail,
                    "conditions": self.conditions,
                    "medications": [m for m in self.medications if m.strip()],
                    "allergies": self.allergies_text if self.allergies_flag else "None",
                    "family_history": self.family_history,
                    "smoking": self.smoking,
                    "alcohol": self.alcohol
                }
                
                resp = await client.post(
                    f"{API_BASE_URL}/session/init",
                    json=payload,
                    headers={"X-API-KEY": API_KEY},
                    timeout=10.0
                )
                if resp.status_code == 200:
                    session_id = resp.json().get("session_id")
                    if not session_id:
                        yield rx.window_alert(self._t["err_generic"] + "Invalid session response from server.")
                        return
                    self.session_id = session_id
                    self.step = 5
                    self.current_answers = []
                    self.questions = []
                    # Auto-trigger interview questions
                    async for item in self.get_interview_questions():
                        yield item
                else:
                    yield rx.window_alert(f"{self._t['err_init']}{resp.text}")
            except Exception as e:
                yield rx.window_alert(f"{self._t['err_generic']}{str(e)}")
            finally:
                self.loading = False

    async def get_interview_questions(self):
        """Step 5 Streaming: Trigger interview questions."""
        self.loading = True
        self._qs_buffer = ""
        self.questions = []
        self.current_answers = []
        yield
        
        async with httpx.AsyncClient() as client:
            try:
                headers = {"X-API-KEY": API_KEY}
                payload = {
                    "session_id": self.session_id
                }
                
                async with client.stream(
                    "POST", 
                    f"{API_BASE_URL}/interview-questions-stream", 
                    json=payload, 
                    headers=headers,
                    timeout=60.0
                ) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            chunk = json.loads(line[len("data: "):])
                            self._qs_buffer += chunk
                            import re
                            # Match lines like "1. Question", "2) Question", etc. Very permissive match
                            qs = [q.strip() for q in re.split(r'\n(?:\d+[\.\)]|\-)\s*', '\n' + self._qs_buffer) if q.strip()]
                            self.questions = qs
                            
                            while len(self.current_answers) < len(self.questions):
                                self.current_answers.append("")
                            yield
            except Exception as e:
                yield rx.window_alert(f"{self._t['err_stream']}{str(e)}")
            finally:
                self.loading = False

    async def submit_answers(self):
        """Step 5 -> Step 6: Finalize."""
        if any(not ans.strip() for ans in self.current_answers[:len(self.questions)]):
            yield rx.window_alert(self._t.get("err_followup_ans", "Please answer all questions."))
            return
        
        # Build plain text summary for clipboard
        qs_ans_text = "\n\n".join(
            f"Q{i+1}: {q}\nA: {a}" 
            for i, (q, a) in enumerate(zip(self.questions, self.current_answers))
        )
        self.summary_text = (
            f"--- Patient Intake ---\n"
            f"Specialist: {self.specialist}\n"
            f"Chief Complaint: {self.chief_complaint}\n\n"
            f"--- Questions & Answers ---\n{qs_ans_text}"
        )
        self.step = 6

    async def download_report(self):
        """Step 6: Securely fetch PDF with API Key and trigger download."""
        self.loading = True
        yield
        
        async with httpx.AsyncClient() as client:
            try:
                headers = {"X-API-KEY": API_KEY}
                payload = {
                    "session_id": self.session_id,
                    "qa_pairs": [
                        {"question": q, "answer": a} 
                        for q, a in zip(self.questions, self.current_answers)
                    ]
                }
                resp = await client.post(
                    f"{API_BASE_URL}/generate-pdf",
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
                    yield rx.window_alert(f"{self._t['err_download']}{resp.text}")
            except Exception as e:
                yield rx.window_alert(f"{self._t['err_download_gen']}{str(e)}")
            finally:
                self.loading = False
