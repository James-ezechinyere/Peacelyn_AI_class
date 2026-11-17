import os
import time
import urllib.parse
import requests
import streamlit as st

ASPECT_DIMENSIONS = {
    "1:1": (1024, 1024),
    "16:9": (1280, 720),
    "4:3": (1024, 768),
    "9:16": (720, 1280),
}

def _get_secret(key_name: str) -> str:
    try:
        return os.getenv(key_name) or st.secrets.get(key_name, "")
    except Exception:
        return os.getenv(key_name, "")

def generate_open_source_image(prompt: str, aspect_ratio: str = "1:1", fallback_reason: str = "") -> tuple[bytes | None, str]:
    """
    Resilient open-source image cascade:
    1. Pollinations (gen.pollinations.ai - FLUX)
    2. Cloudflare Workers AI (FLUX.1-schnell, if CF_ACCOUNT_ID & CF_API_TOKEN set)
    3. AI Horde (Zero-key community Stable Diffusion fallback)
    """
    width, height = ASPECT_DIMENSIONS.get(aspect_ratio, (1024, 1024))
    clean_prompt = prompt.strip()
    encoded_prompt = urllib.parse.quote(clean_prompt)
    prefix = "*(Gemini busy — switched to open-source FLUX)*\n\n" if fallback_reason else ""

    # --- TIER 1: Pollinations Current Gateway (gen.pollinations.ai) ---
    pollinations_key = _get_secret("POLLINATIONS_API_KEY")
    try:
        url = (
            f"https://gen.pollinations.ai/image/{encoded_prompt}"
            f"?model=flux&width={width}&height={height}&nologo=true"
        )
        headers = {"Authorization": f"Bearer {pollinations_key}"} if pollinations_key else {}
        res = requests.get(url, headers=headers, timeout=40)
        if res.status_code == 200 and res.headers.get("content-type", "").startswith("image/"):
            return res.content, f"{prefix}✨ Generated with **FLUX.1 (Pollinations)** ({aspect_ratio})"
    except Exception:
        pass

    # --- TIER 2: Cloudflare Workers AI (Free Daily Tier) ---
    cf_account = _get_secret("CF_ACCOUNT_ID")
    cf_token = _get_secret("CF_API_TOKEN")
    if cf_account and cf_token:
        try:
            cf_url = f"https://api.cloudflare.com/client/v4/accounts/{cf_account}/ai/run/@cf/black-forest-labs/flux-1-schnell"
            cf_headers = {"Authorization": f"Bearer {cf_token}"}
            cf_res = requests.post(cf_url, headers=cf_headers, json={"prompt": clean_prompt}, timeout=40)
            if cf_res.status_code == 200:
                if cf_res.headers.get("content-type", "").startswith("image/"):
                    return cf_res.content, f"{prefix}✨ Generated with **FLUX.1-schnell (Cloudflare)** ({aspect_ratio})"
                data = cf_res.json()
                b64_img = data.get("result", {}).get("image")
                if b64_img:
                    import base64
                    return base64.b64decode(b64_img), f"{prefix}✨ Generated with **FLUX.1-schnell (Cloudflare)** ({aspect_ratio})"
        except Exception:
            pass

    # --- TIER 3: AI Horde (100% Free, Zero-Key Anonymous Cluster) ---
    try:
        horde_headers = {
            "apikey": "0000000000",
            "Client-Agent": "SchoolAIStudio:1.0:teacher@school.edu"
        }
        payload = {
            "prompt": clean_prompt,
            "params": {
                "width": 512,
                "height": 512,
                "steps": 20,
                "n": 1
            }
        }
        submit_res = requests.post(
            "https://aihorde.net/api/v2/generate/async",
            headers=horde_headers,
            json=payload,
            timeout=15
        )
        if submit_res.status_code == 202:
            req_id = submit_res.json().get("id")
            # Poll up to 45 seconds for community worker completion
            for _ in range(15):
                time.sleep(3)
                status_res = requests.get(f"https://aihorde.net/api/v2/generate/status/{req_id}", timeout=10)
                status_data = status_res.json()
                if status_data.get("done") and status_data.get("generations"):
                    img_url = status_data["generations"][0].get("img")
                    if img_url:
                        img_file = requests.get(img_url, timeout=20)
                        if img_file.status_code == 200:
                            return img_file.content, f"{prefix}✨ Generated with **AI Horde Open Cluster** (512×512)"
                    break
    except Exception:
        pass

    return None, "⚠️ All image generators are currently busy. Please wait 10 seconds and try again!"