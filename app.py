import uuid
import streamlit as st
import matplotlib.pyplot as plt
from config import DAILY_TOPIC, CLASS_CAPSTONES
from database import DatabaseService
from ai_service import get_ai_service  # <--- Clean factory import

st.set_page_config(page_title="AI Prompt Engineering Virtual Lab", page_icon="🎓", layout="wide")

db = DatabaseService()

# --- SIDEBAR SELECTOR & FACTORY INSTANTIATION ---
st.sidebar.title("⚙️ Model Platform Selector")
platform_choice = st.sidebar.selectbox("Choose AI Provider:", ["OpenRouter", "Groq", "Gemini"])

# Dynamically instantiate the chosen provider using the factory function
ai_service = get_ai_service(platform_choice)

if platform_choice == "OpenRouter":
    model_to_use = "meta-llama/llama-3.1-70b-instruct"
elif platform_choice == "Groq":
    model_to_use = "openai/gpt-oss-20b"
else:
    model_to_use = "gemini-2.5-flash"

# Session State Initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "student_name" not in st.session_state:
    st.session_state.student_name = ""
if "grade_class" not in st.session_state:
    st.session_state.grade_class = "JS1 (Grade 7)"
if "active_session_id" not in st.session_state:
    st.session_state.active_session_id = str(uuid.uuid4())[:8]
if "last_evaluation" not in st.session_state:
    st.session_state.last_evaluation = None

# ==========================================
# PAGE 1: LOGIN / SIGNUP SCREEN
# ==========================================
if not st.session_state.authenticated:
    st.title("🎓 AI Prompt Engineering Virtual Lab")
    st.markdown("### Student Authentication Portal")
    
    with st.form("auth_form"):
        name_input = st.text_input("Full Name:")
        class_input = st.selectbox("Select Your Class:", list(CLASS_CAPSTONES.keys()))
        password_input = st.text_input("Password (Stored for easy recovery if forgotten):", type="default")
        
        submit_btn = st.form_submit_button("Login / Create Account", type="primary")
        
        if submit_btn:
            if name_input.strip() and password_input.strip():
                if db.authenticate_user(name_input.strip(), class_input, password_input.strip()):
                    st.session_state.authenticated = True
                    st.session_state.student_name = name_input.strip()
                    st.session_state.grade_class = class_input
                    st.rerun()
            else:
                st.warning("Please enter both your name and password.")

# ==========================================
# PAGE 2: MAIN LAB DASHBOARD & CHAT WORKSPACE
# ==========================================
else:
    capstone = CLASS_CAPSTONES[st.session_state.grade_class]

    st.sidebar.markdown("---")
    st.sidebar.title(f"👤 {st.session_state.student_name}")
    st.sidebar.markdown(f"**Class:** `{st.session_state.grade_class}`")
    
    if st.sidebar.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💬 Previous Chat Sessions")
    
    if st.sidebar.button("➕ Start New Prompt Session"):
        st.session_state.active_session_id = str(uuid.uuid4())[:8]
        st.session_state.last_evaluation = None
        st.rerun()

    previous_sessions = db.get_student_sessions(st.session_state.student_name, st.session_state.grade_class)
    
    for sess in previous_sessions:
        s_id = sess["session_id"]
        highest = sess.get("highest_score", 0)
        label = f"Session {s_id} (Best: {highest}/100)"
        if st.sidebar.button(label, key=s_id):
            st.session_state.active_session_id = s_id
            history = sess.get("history", [])
            if history:
                last_entry = history[-1]
                stored_feedback = last_entry.get("feedback", {})
                
                # Ensure it handles both old string format and new dictionary format gracefully
                if isinstance(stored_feedback, dict):
                    feedback_payload = stored_feedback
                else:
                    feedback_payload = {
                        "score": last_entry["score"],
                        "strengths": "Retrieved from saved session history.",
                        "weaknesses": "Review past performance metrics.",
                        "tips": str(stored_feedback)
                    }

                st.session_state.last_evaluation = {
                    "prompt": last_entry["prompt"],
                    "response": last_entry["response"],
                    "score": last_entry["score"],
                    "feedback": feedback_payload
                }
            st.rerun()

    # --- MAIN CONTENT AREA ---
    st.title("⚡ AI Prompt Engineering Lab")
    st.info(f"**Today's Universal Lesson Topic:** {DAILY_TOPIC} | **Active Engine:** `{platform_choice}`")

    with st.expander(f"🏆 Class Capstone Project: {capstone['capstone_title']}", expanded=False):
        st.markdown(f"**Objective:** {capstone['objective']}")
        st.markdown(f"**Judge Criteria:** *{capstone['eval_criteria']}*")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### ✍️ Prompt Workspace")
        student_prompt = st.text_area(
            "Construct your structured prompt (Apply C.I.I.O. framework):",
            height=220,
            placeholder="Context: Act as...\nInstruction: ...\nInput Data: ...\nOutput Format: ..."
        )

        submit_prompt = st.button("🚀 Evaluate Prompt", type="primary")

        if submit_prompt:
            if not student_prompt.strip():
                st.warning("Please enter a prompt before submitting.")
            else:
                with st.spinner(f"🤖 Generating via {platform_choice} and running Judge evaluation..."):
                    llm_output = ai_service.generate_response(student_prompt, model_to_use)
                    score, eval_dict = ai_service.evaluate_prompt(student_prompt, llm_output, st.session_state.grade_class, capstone)
                    
                    db.save_chat_session(
                        student_name=st.session_state.student_name,
                        grade_class=st.session_state.grade_class,
                        session_id=st.session_state.active_session_id,
                        prompt=student_prompt,
                        response=llm_output,
                        score=score,
                        feedback=eval_dict  # <--- Matches the 'feedback' keyword parameter
                    )

                    st.session_state.last_evaluation = {
                        "prompt": student_prompt,
                        "response": llm_output,
                        "score": score,
                        "feedback": eval_dict
                    }
                st.rerun()

    with col2:
        st.markdown("### 📊 Evaluation & Results")
        
        if st.session_state.last_evaluation:
            eval_data = st.session_state.last_evaluation
            score = eval_data["score"]
            feedback = eval_data["feedback"]

            # Score Pie Chart
            fig, ax = plt.subplots(figsize=(3, 3))
            colors = ['#4CAF50' if score >= 70 else '#FF9800' if score >= 40 else '#F44336', '#E0E0E0']
            ax.pie([score, max(0, 100 - score)], colors=colors, startangle=90, counterclock=False)
            ax.set_title(f"Score: {score}/100", fontsize=12, fontweight='bold')
            st.pyplot(fig)

            session_records = db.get_student_sessions(st.session_state.student_name, st.session_state.grade_class)
            current_sess_data = next((s for s in session_records if s["session_id"] == st.session_state.active_session_id), None)
            highest_score = current_sess_data.get("highest_score", score) if current_sess_data else score

            st.metric(label="Highest Score Recorded for This Session", value=f"{highest_score} / 100")

            with st.expander("🔍 View Detailed Feedback & AI Response", expanded=True):
                st.markdown(f"**AI Response Preview:**\n> {eval_data['response'][:300]}...")
                st.markdown(f"**💪 Strengths:**\n{feedback.get('strengths', 'N/A')}")
                st.markdown(f"**⚠️ Weaknesses:**\n{feedback.get('weaknesses', 'N/A')}")
                st.markdown(f"**💡 Improvement Tips:**\n{feedback.get('tips', 'N/A')}")
        else:
            st.info("Submit a prompt in the workspace to see your score pie chart and feedback report.")