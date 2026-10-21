import os
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
# # --- ADD THESE DEBUG PRINTS ---
# print("DEBUG - SUPABASE_URL:", repr(SUPABASE_URL))
# print("DEBUG - SUPABASE_KEY type:", type(SUPABASE_KEY))

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

class DatabaseService:
    def __init__(self):
        self.supabase = init_supabase()

    def authenticate_user(self, name: str, grade_class: str, password: str) -> bool:
        """Checks if user exists. If yes, verifies plain-text password. If no, creates account."""
        try:
            response = self.supabase.table("students").select("*").eq("name", name).eq("grade_class", grade_class).execute()
            users = response.data

            if users:
                # Existing user -> verify password
                stored_user = users[0]
                if stored_user["password"] == password:
                    return True
                else:
                    st.error("Incorrect password for this name and class.")
                    return False
            else:
                # New user -> sign up (store plain-text password)
                self.supabase.table("students").insert({
                    "name": name,
                    "grade_class": grade_class,
                    "password": password
                }).execute()
                st.success("Account created successfully! Logging you in...")
                return True
        except Exception as e:
            st.error(f"Database connection error: {e}")
            return False

    def save_chat_session(self, student_name: str, grade_class: str, session_id: str, prompt: str, response: str, score: float, feedback: dict):
        """Saves or updates a chat session in Supabase with the full evaluation dictionary."""
        try:
            existing = self.supabase.table("chat_sessions").select("*").eq("session_id", session_id).execute()
            
            chat_entry = {
                "prompt": prompt,
                "response": response,
                "score": score,
                "feedback": feedback  # Uses the dictionary passed directly
            }

            if existing.data:
                current_data = existing.data[0]
                history = current_data.get("history", [])
                history.append(chat_entry)
                
                highest_score = max(current_data.get("highest_score", 0), score)

                self.supabase.table("chat_sessions").update({
                    "history": history,
                    "highest_score": highest_score
                }).eq("session_id", session_id).execute()
            else:
                self.supabase.table("chat_sessions").insert({
                    "session_id": session_id,
                    "student_name": student_name,
                    "grade_class": grade_class,
                    "history": [chat_entry],
                    "highest_score": score
                }).execute()
        except Exception as e:
            st.error(f"Failed to save chat session: {e}")

    def get_student_sessions(self, student_name: str, grade_class: str):
        """Retrieves all previous chat sessions for a specific student."""
        try:
            response = self.supabase.table("chat_sessions").select("*").eq("student_name", student_name).eq("grade_class", grade_class).execute()
            return response.data
        except Exception as e:
            return []