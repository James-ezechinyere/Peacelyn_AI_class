import uuid
import base64
import streamlit as st
from config import GRADE_WORKSPACES
from database import DatabaseService
from ai_service import get_ai_service
from architect import synthesize_lovable_master_prompt

st.set_page_config(page_title="AI Creative & Research Studio", page_icon="✨", layout="wide")

db = DatabaseService()

# Session State Initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "student_name" not in st.session_state:
    st.session_state.student_name = ""
if "grade_class" not in st.session_state:
    st.session_state.grade_class = "JS1 (Grade 7)"
if "active_session_id" not in st.session_state:
    st.session_state.active_session_id = str(uuid.uuid4())[:8]
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# ==========================================
# AUTHENTICATION SCREEN
# ==========================================
if not st.session_state.authenticated:
    st.title("🎓 Student AI Studio Sign-In")
    st.markdown("Enter your name and class to open your AI workspace.")
    
    with st.form("auth_form"):
        name_input = st.text_input("Full Name:")
        grade_input = st.selectbox("Select Your Class:", list(GRADE_WORKSPACES.keys()))
        submit_auth = st.form_submit_button("Start Session 🚀", type="primary")
        
        if submit_auth:
            if name_input.strip():
                st.session_state.student_name = name_input.strip()
                st.session_state.grade_class = grade_input
                db.authenticate_student(st.session_state.student_name, st.session_state.grade_class)
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.warning("Please enter your full name.")

# ==========================================
# MAIN CONVERSATIONAL WORKSPACE
# ==========================================
else:
    workspace = GRADE_WORKSPACES[st.session_state.grade_class]
    mode = workspace["mode"]

    # --- SIDEBAR ---
    st.sidebar.title("⚙️ AI Engine")
    default_idx = 0 if mode == "image_studio" else 0
    platform_choice = st.sidebar.selectbox("Provider:", ["Gemini", "Groq", "OpenRouter"], index=default_idx)
    ai_service = get_ai_service(platform_choice)

    if platform_choice == "OpenRouter":
        model_to_use = "anthropic/claude-3.5-sonnet"
    elif platform_choice == "Groq":
        model_to_use = "llama-3.3-70b-versatile"
    else:
        model_to_use = "gemini-2.5-flash"

    aspect_ratio = "1:1"
    if mode == "image_studio":
        aspect_ratio = st.sidebar.selectbox("🖼️ Image Aspect Ratio:", ["1:1", "16:9", "4:3", "9:16"])

    st.sidebar.markdown("---")
    st.sidebar.title(f"👤 {st.session_state.student_name}")
    st.sidebar.markdown(f"**Class:** `{st.session_state.grade_class}`")

    if st.sidebar.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.chat_messages = []
        st.rerun()

    if mode != "ss1_web_studio":
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 💬 Chat History")
        if st.sidebar.button("➕ New Chat", use_container_width=True):
            st.session_state.active_session_id = str(uuid.uuid4())[:8]
            st.session_state.chat_messages = []
            st.rerun()

        previous_sessions = db.get_student_sessions(st.session_state.student_name, st.session_state.grade_class)
        for sess in previous_sessions:
            s_id = sess["session_id"]
            hist = sess.get("history", [])
            preview = hist[0]["content"][:24] + "..." if hist and hist[0].get("content") else f"Chat {s_id}"
            if st.sidebar.button(f"💭 {preview}", key=s_id, use_container_width=True):
                st.session_state.active_session_id = s_id
                st.session_state.chat_messages = hist
                st.rerun()

    # ==========================================
    # ROUTE 1: SS1 COLLABORATIVE WEB STUDIO
    # ==========================================
    if mode == "ss1_web_studio":
        st.title(workspace["title"])
        st.caption(workspace["subtitle"])

        features = db.get_all_features()
        student_name = st.session_state.student_name

        my_feature = next((f for f in features if student_name in (f.get("assigned_students") or [])), None)

        if not my_feature:
            st.subheader("1️⃣ Choose Your Feature Module (Pair Programming Welcome)")
            st.info("You can join a feature team where other students are already working, or pick an available one!")
            
            for feat in features:
                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])
                    contributors = feat.get("assigned_students") or []
                    col1.markdown(f"**{feat['feature_title']}**")
                    col1.write(feat["feature_brief"])
                    if contributors:
                        col1.caption(f"👥 Current Team: {', '.join(contributors)}")
                    else:
                        col1.caption("⚡ Unclaimed - Be the first to join!")
                        
                    if col2.button("Join / Claim", key=f"join_{feat['feature_key']}", use_container_width=True):
                        if db.join_feature_team(feat["feature_key"], student_name):
                            st.rerun()
        
        else:
            st.success(f"🛠️ Your Feature Team: **{my_feature['feature_title']}**")
            st.markdown(f"**Design Brief:** {my_feature['feature_brief']}")
            team_members = my_feature.get("assigned_students", [])
            st.markdown(f"👥 **Teammates working on this:** {', '.join(team_members)}")

            submitted_prompts = my_feature.get("student_prompts") or {}
            if submitted_prompts:
                with st.expander("👀 View Teammates' Submitted Final Prompts"):
                    for mate, p_text in submitted_prompts.items():
                        st.markdown(f"**{mate}:** {p_text}")

            st.markdown("---")
            st.markdown("### 💬 AI Mentor & Brainstorming Studio")
            st.caption(f"Brainstorm ideas, layout structure, and user experience with your AI mentor. **(Note: The AI will help you brainstorm concepts, not write code!)**")

            # Initialize local session state for this feature's chat if not present
            if "feature_chat_msgs" not in st.session_state or st.session_state.get("active_feature_key") != my_feature["feature_key"]:
                st.session_state.active_feature_key = my_feature["feature_key"]
                st.session_state.feature_chat_msgs = my_feature.get("feature_chat_history") or []

            # Display chat history cleanly
            for msg in st.session_state.feature_chat_msgs:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            # Brainstorming Input & Action Buttons side-by-side
            chat_prompt = st.text_input("Ask AI for ideas, layout advice, or features:", placeholder="e.g., What elements should we put in our navigation bar?", key="chat_input_box")
            
            c_btn1, c_btn2 = st.columns(2)
            send_chat = c_btn1.button("Send to AI Mentor 💬", use_container_width=True)
            generate_prompt_btn = c_btn2.button("✨ Generate Prompt from Chat", use_container_width=True)

            # Handle Sending Chat to AI
            if send_chat and chat_prompt.strip():
                st.session_state.feature_chat_msgs.append({"role": "user", "content": chat_prompt})
                
                with st.spinner("AI Mentor is brainstorming with you..."):
                    sys_instruction = (
                        f"You are an encouraging educational design mentor helping high school students build "
                        f"a School Project Showcase website (Grade 3 to SS2). "
                        f"The student is currently working on: '{my_feature['feature_title']}'. "
                        f"Design Brief: {my_feature['feature_brief']}. "
                        f"CRITICAL RULE: Do NOT write code, HTML structures, or Tailwind CSS classes. "
                        f"Instead, brainstorm with them conceptually. Give them ideas on what visual elements to include, "
                        f"how users will interact with the feature, layout structures, and creative design suggestions."
                    )
                    ai_reply = ai_service.chat(st.session_state.feature_chat_msgs, model_to_use, system_instruction=sys_instruction)
                    st.session_state.feature_chat_msgs.append({"role": "assistant", "content": ai_reply})

                db.save_feature_chat(my_feature["feature_key"], st.session_state.feature_chat_msgs)
                st.rerun()

            # --- HANDLE "GENERATE PROMPT" FROM CHAT ---
            draft_key = f"draft_prompt_{my_feature['feature_key']}"
            
            if draft_key not in st.session_state:
                st.session_state[draft_key] = submitted_prompts.get(student_name, "")

            if generate_prompt_btn:
                if st.session_state.feature_chat_msgs:
                    with st.spinner("Synthesizing your brainstorming chat into a clean final prompt..."):
                        summary_query = (
                            f"Based on our entire brainstorming chat above for '{my_feature['feature_title']}', "
                            f"write a clean, professional, and detailed feature prompt/specification that I can submit as my final work. "
                            f"Focus purely on the visual requirements, user experience, and layout details discussed."
                        )
                        temp_history = st.session_state.feature_chat_msgs + [{"role": "user", "content": summary_query}]
                        synthesized_prompt = ai_service.chat(temp_history, model_to_use)
                        st.session_state[draft_key] = synthesized_prompt
                    st.success("✨ Prompt successfully generated! Scroll down to review and submit.")
                    st.rerun()
                else:
                    st.warning("Chat with the AI mentor first before generating a prompt!")

            st.markdown("---")
            st.markdown("### ✍️ Final Feature Prompt Submission")
            st.caption("Review your generated prompt below (or type/edit your final instructions), then submit. It will automatically merge with your teammates' prompts!")
            
            final_pasted_input = st.text_area(
                "Your Final Feature Specification:", 
                value=st.session_state[draft_key], 
                height=180, 
                key=f"textarea_{draft_key}"
            )

            if final_pasted_input != st.session_state[draft_key]:
                st.session_state[draft_key] = final_pasted_input

            if st.button("🚀 Submit & Merge Final Prompt", type="primary"):
                if len(st.session_state[draft_key].strip()) >= 15:
                    db.submit_and_merge_prompt(my_feature["feature_key"], student_name, st.session_state[draft_key].strip(), ai_service, model_to_use)
                    st.success("🎉 Success! Your prompt was successfully submitted and merged into your team's master specification.")
                    st.rerun()
                else:
                    st.warning("Please provide a bit more detail before submitting.")

            if my_feature.get("aggregated_prompt"):
                with st.expander("✨ View Current Merged Team Specification"):
                    st.markdown(my_feature["aggregated_prompt"])

        # --- STEP C: TEACHER BUILD CONTROLS ---
        st.markdown("---")
        st.subheader("📊 SS1 Live Engineering Board")
        features_updated = db.get_all_features()
        submitted_teams = sum(1 for f in features_updated if f["status"] == "submitted")
        total_teams = len(features_updated)
        st.progress(submitted_teams / total_teams if total_teams else 0, text=f"{submitted_teams} of {total_teams} Feature Teams Ready")

        for f in features_updated:
            icon = "✅" if f["status"] == "submitted" else ("⏳" if f["status"] == "claimed" else "⬜")
            team = ", ".join(f.get("assigned_students") or []) or "Unclaimed"
            st.markdown(f"{icon} **{f['feature_title']}** — *Team: {team}*")

        with st.expander("🎓 Teacher / Build Master Controls"):
            TEACHER_PIN = "Ezechinyere001"
            
            teacher_pin_input = st.text_input("Enter Teacher PIN:", type="password")
            if teacher_pin_input == TEACHER_PIN:
                c1, c2 = st.columns([3, 1])
                if c1.button("🧠 Combine All Team Specs & Generate Lovable Link", type="primary"):
                    with st.spinner("Principal AI Architect is merging all team prompts into a master build..."):
                        mp, url = synthesize_lovable_master_prompt(ai_service, model_to_use, features_updated)
                        st.session_state.master_lovable_prompt = mp
                        st.session_state.master_lovable_url = url
                if c2.button("🔄 Reset All Boards"):
                    db.reset_all_features()
                    st.rerun()

                if "master_lovable_url" in st.session_state:
                    st.success("Master Specification Ready across all teams!")
                    st.link_button("🚀 Open & Auto-Build in Lovable", st.session_state.master_lovable_url, type="primary")
                    st.text_area("Combined Master Prompt:", value=st.session_state.master_lovable_prompt, height=220)
            elif teacher_pin_input:
                st.error("Incorrect PIN.")

    # ==========================================
    # ROUTE 2: CONVERSATIONAL CHAT STUDIOS
    # ==========================================
    else:
        st.title(workspace["title"])
        st.caption(workspace["subtitle"])

        for idx, msg in enumerate(st.session_state.chat_messages):
            with st.chat_message(msg["role"]):
                if msg.get("thoughts"):
                    with st.expander("🧠 View Agent Thinking & Research Process"):
                        st.markdown(msg["thoughts"])
                if msg.get("content"):
                    st.markdown(msg["content"])
                if msg.get("image_b64"):
                    img_data = base64.b64decode(msg["image_b64"])
                    st.image(img_data, use_container_width=True)
                    st.download_button(
                        label="⬇️ Download Image",
                        data=img_data,
                        file_name=f"ai_art_{idx}.png",
                        mime="image/png",
                        key=f"dl_{idx}"
                    )

        if prompt := st.chat_input(workspace["placeholder"]):
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                if mode == "image_studio":
                    with st.spinner("🎨 Generating your image (Gemini ➔ FLUX Fallback)..."):
                        img_bytes, caption = ai_service.generate_image(prompt, aspect_ratio=aspect_ratio)
                        assistant_msg = {"role": "assistant", "content": caption}
                        if img_bytes:
                            st.image(img_bytes, use_container_width=True)
                            b64_str = base64.b64encode(img_bytes).decode("utf-8")
                            assistant_msg["image_b64"] = b64_str
                            st.download_button(
                                label="⬇️ Download Image",
                                data=img_bytes,
                                file_name="generated_art.png",
                                mime="image/png"
                            )
                        if caption:
                            st.markdown(caption)
                        st.session_state.chat_messages.append(assistant_msg)

                elif mode == "reasoning_agent":
                    with st.spinner("🔬 Researching and reasoning deeply..."):
                        thoughts, answer = ai_service.research_with_reasoning(st.session_state.chat_messages, model_to_use)
                        if thoughts:
                            with st.expander("🧠 View Agent Thinking & Research Process", expanded=True):
                                st.markdown(thoughts)
                        st.markdown(answer)
                        st.session_state.chat_messages.append({
                            "role": "assistant",
                            "content": answer,
                            "thoughts": thoughts
                        })

                else:
                    with st.spinner("Thinking..."):
                        reply = ai_service.chat(st.session_state.chat_messages, model_to_use)
                        st.markdown(reply)
                        st.session_state.chat_messages.append({
                            "role": "assistant",
                            "content": reply
                        })

            db.save_conversation(
                student_name=st.session_state.student_name,
                grade_class=st.session_state.grade_class,
                session_id=st.session_state.active_session_id,
                messages=st.session_state.chat_messages
            )