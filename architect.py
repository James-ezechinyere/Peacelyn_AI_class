import urllib.parse
from ai_service.base import AIProvider

def synthesize_lovable_master_prompt(ai_service: AIProvider, model_name: str, features: list) -> tuple[str, str]:
    """
    Combines all SS1 student feature prompts into a single cohesive master prompt
    and generates a Lovable Build-with-URL link.
    """
    submitted_blocks = []
    for f in features:
        if f.get("student_prompt"):
            submitted_blocks.append(
                f"### Feature Module: {f['feature_title']} (Engineered by {f['assigned_student']})\n"
                f"{f['student_prompt']}"
            )
        else:
            # Fallback if a module wasn't submitted yet so the site stays complete
            submitted_blocks.append(
                f"### Feature Module: {f['feature_title']} (Standard Spec)\n"
                f"{f['feature_brief']}"
            )

    combined_specs = "\n\n".join(submitted_blocks)

    architect_system_instruction = """
You are a Principal Full-Stack Software Architect preparing a master specification prompt for Lovable (an AI full-stack React + Tailwind CSS + Supabase app builder).

Your job is to merge multiple feature prompts written by SS1 high school students into ONE unified, cohesive, non-contradictory prompt for a **School Project Showcase Platform (Grade 3 to SS2)**.

Rules for synthesis:
1. Enforce a single unified visual theme, color palette, and responsive Tailwind CSS layout across all modules so the website looks like one seamless product, not stitched-together parts.
2. Explicitly ensure every project card and modal displays the **Project Title**, **Creator's Full Name**, **Grade Level (Grade 3 through SS2)**, **Category**, and **Description**.
3. Include realistic sample student projects across Grade 3, Grade 5, JS1, JS2, SS1, and SS2 so the site looks alive immediately upon build.
4. Keep the final output under 4,500 characters so it fits cleanly into URL parameters while remaining richly detailed.
5. Output ONLY the final Lovable prompt text—no conversational filler before or after.
"""

    full_input = f"{architect_system_instruction}\n\nHere are the student-engineered feature specifications:\n\n{combined_specs}"
    
    master_prompt = ai_service.generate_response(full_input, model_name).strip()

    # Encode for Lovable's Build-with-URL API (auto-submits in browser)
    encoded_prompt = urllib.parse.quote(master_prompt)
    lovable_url = f"https://lovable.dev/?autosubmit=true#prompt={encoded_prompt}"

    return master_prompt, lovable_url