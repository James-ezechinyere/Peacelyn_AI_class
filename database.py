import os
import base64
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")

@st.cache_resource
def init_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("CRITICAL: Supabase URL or Key is missing.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

class DatabaseService:
    def __init__(self):
        self.supabase = init_supabase()

    def authenticate_student(self, student_name: str, grade_class: str) -> bool:
        try:
            res = self.supabase.table("students").select("*").eq("student_name", student_name).execute()
            if not res.data:
                self.supabase.table("students").insert({
                    "student_name": student_name,
                    "grade_class": grade_class
                }).execute()
            return True
        except Exception as e:
            st.error(f"Database authentication error: {e}")
            return False

    def save_conversation(self, student_name: str, grade_class: str, session_id: str, messages: list[dict]):
        """Persists the full chat conversation (including reasoning thoughts and compressed thumbnails) to Supabase."""
        try:
            # Strip raw bytes before JSONB serialization; keep base64 thumbnail if present
            serializable_msgs = []
            for m in messages:
                entry = {
                    "role": m["role"],
                    "content": m.get("content", ""),
                }
                if m.get("thoughts"):
                    entry["thoughts"] = m["thoughts"]
                if m.get("image_b64"):
                    entry["image_b64"] = m["image_b64"]
                serializable_msgs.append(entry)

            existing = self.supabase.table("chat_sessions").select("*").eq("session_id", session_id).execute()
            if existing.data:
                self.supabase.table("chat_sessions").update({
                    "history": serializable_msgs
                }).eq("session_id", session_id).execute()
            else:
                self.supabase.table("chat_sessions").insert({
                    "session_id": session_id,
                    "student_name": student_name,
                    "grade_class": grade_class,
                    "history": serializable_msgs,
                    "highest_score": 0
                }).execute()
        except Exception as e:
            st.error(f"Failed to save conversation: {e}")

    def get_student_sessions(self, student_name: str, grade_class: str):
        try:
            res = (
                self.supabase.table("chat_sessions")
                .select("*")
                .eq("student_name", student_name)
                .eq("grade_class", grade_class)
                .order("created_at", desc=True)
                .execute()
            )
            return res.data or []
        except Exception:
            return []

    def get_all_features(self):
        try:
            res = self.supabase.table("ss1_feature_modules").select("*").order("id").execute()
            return res.data or []
        except Exception:
            return []

    def join_feature_team(self, feature_key: str, student_name: str) -> bool:
        """Allows a student to join a feature module team (enabling pair programming)."""
        try:
            feat = self.supabase.table("ss1_feature_modules").select("assigned_students, status").eq("feature_key", feature_key).execute()
            if not feat.data:
                return False
            
            current_students = feat.data[0].get("assigned_students") or []
            if student_name not in current_students:
                current_students.append(student_name)
            
            self.supabase.table("ss1_feature_modules").update({
                "assigned_students": current_students,
                "status": "claimed"
            }).eq("feature_key", feature_key).execute()
            return True
        except Exception:
            return False

    def save_feature_chat(self, feature_key: str, chat_history: list):
        """Saves the shared brainstorming chat history for a feature module."""
        try:
            self.supabase.table("ss1_feature_modules").update({
                "feature_chat_history": chat_history
            }).eq("feature_key", feature_key).execute()
        except Exception:
            pass

    def submit_and_merge_prompt(self, feature_key: str, student_name: str, student_prompt: str, ai_service, model_name: str):
        """Saves a student's prompt and uses AI to merge it with previous submissions for this feature."""
        try:
            res = self.supabase.table("ss1_feature_modules").select("student_prompts, aggregated_prompt, feature_title").eq("feature_key", feature_key).execute()
            if not res.data:
                return
            
            row = res.data[0]
            prompts_dict = row.get("student_prompts") or {}
            prompts_dict[student_name] = student_prompt

            # Combine all student prompts submitted for this feature so far
            all_submitted_texts = "\n\n".join([f"Contributor ({name}): {txt}" for name, txt in prompts_dict.items()])

            # Use AI to intelligently merge them into a single coherent feature spec
            merge_query = (
                f"You are a Lead Software Architect. Combine these individual student feature specifications "
                f"for '{row['feature_title']}' into one unified, non-contradictory, highly detailed UI/UX prompt. "
                f"Incorporate all ideas smoothly:\n\n{all_submitted_texts}"
            )
            
            merged_result = ai_service.chat([{"role": "user", "content": merge_query}], model_name)

            self.supabase.table("ss1_feature_modules").update({
                "student_prompts": prompts_dict,
                "aggregated_prompt": merged_result,
                "status": "submitted"
            }).eq("feature_key", feature_key).execute()
        except Exception as e:
            st.error(f"Failed to merge prompt: {e}")

    def reset_all_features(self):
        try:
            self.supabase.table("ss1_feature_modules").update({
                "assigned_students": [],
                "feature_chat_history": [],
                "student_prompts": {},
                "aggregated_prompt": "",
                "status": "available"
            }).neq("id", 0).execute()
        except Exception:
            pass

    def claim_feature(self, feature_key: str, student_name: str) -> bool:
        try:
            existing = self.supabase.table("ss1_feature_modules").select("*").eq("assigned_student", student_name).execute()
            if existing.data:
                return True
            res = (
                self.supabase.table("ss1_feature_modules")
                .update({"assigned_student": student_name, "status": "claimed"})
                .eq("feature_key", feature_key)
                .eq("status", "available")
                .execute()
            )
            return len(res.data) > 0
        except Exception:
            return False