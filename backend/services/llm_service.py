import requests
import json
import os
import re
import urllib3
from loguru import logger
from typing import List

# Suppress SSL warnings when verify=False is used (common in corp/VPN environments)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class LLMService:
    def __init__(self):
        # Updated defaults to use Aliyun DashScope (Qwen) as provided by user
        self.api_key = os.getenv("LLM_API_KEY", "sk-xxx")
        self.base_url = os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.model_name = os.getenv("LLM_MODEL", "qwen-plus")
        self.batch_size = int(os.getenv("LLM_TRANSLATE_BATCH_SIZE", "30"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.15"))

    def _translate_batch(self, batch_segments: List[dict], target_lang: str) -> List[dict]:
        numbered = "\n".join([f"{i}|{s['text']}" for i, s in enumerate(batch_segments)])

        system_prompt = f"""
You are a professional subtitle translator.
Translate each line into {target_lang}.

Hard rules:
1) Keep exactly one output line for each input line.
2) Keep the same index on each line.
3) Output format strictly: Index|Translated_Text
4) Do not merge lines, do not skip lines, do not add comments.
5) Keep subtitle style concise and natural for spoken language.
6) Preserve entities (names, brands, numbers).
""".strip()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": numbered}
            ],
            "stream": False,
            "temperature": self.temperature
        }

        url = f"{self.base_url}/chat/completions"
        response = requests.post(url, headers=headers, json=data, timeout=90, verify=False)
        response.raise_for_status()

        result_json = response.json()
        translated_block = result_json['choices'][0]['message']['content'].strip()

        translated_map = {}
        for line in translated_block.splitlines():
            if '|' not in line:
                continue
            parts = line.split('|', 1)
            if len(parts) != 2:
                continue
            idx_str = re.sub(r"[^0-9]", "", parts[0].strip())
            if not idx_str.isdigit():
                continue
            translated_map[int(idx_str)] = parts[1].strip()

        merged = []
        for i, seg in enumerate(batch_segments):
            new_seg = seg.copy()
            new_seg["original_text"] = seg.get("text", "")
            translated_text = translated_map.get(i, seg.get("text", ""))
            if not translated_text or not str(translated_text).strip():
                translated_text = seg.get("text", "")
            new_seg["text"] = translated_text
            merged.append(new_seg)
        return merged

    def translate_segments(self, segments: List[dict], target_lang: str = "English") -> List[dict]:
        """
        Translates a list of subtitle segments using an LLM.
        Directly uses 'requests' to avoid incompatible 'openai'/'httpx' library versions.
        """
        
        # --- Check for Valid API Key ---
        if not self.api_key or self.api_key.strip() == "sk-xxx":
            logger.warning("⚠️ No valid LLM_API_KEY found. Skipping translation (Mock Mode - Returns Original Text).")
            return [{"start": s["start"], "end": s["end"], "text": s["text"]} for s in segments]

        logger.info(f"Translating {len(segments)} segments into {target_lang} using requests in batches...")

        try:
            translated_segments = []
            for start in range(0, len(segments), self.batch_size):
                batch = segments[start:start + self.batch_size]
                translated_segments.extend(self._translate_batch(batch, target_lang))

            logger.success(f"Successfully translated {len(translated_segments)} segments.")
            return translated_segments

        except Exception as e:
            logger.error(f"LLM Translation failed (requests): {e}")
            if 'response' in locals() and hasattr(response, 'text'):
                logger.error(f"Response content: {response.text}")
            # Fallback to original text on failure to verify pipeline flow
            return segments

llm_service = LLMService()
