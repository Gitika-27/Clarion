import os
import json
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])

MODEL = "openai/gpt-oss-120b"  # good general-purpose Groq model; swap if you prefer another

SYSTEM_PROMPT = """You are a product data enrichment engine for an industrial \
parts catalog. Given a raw, abbreviated product description and manufacturer \
info, produce a structured JSON object. Rules:
- Only use information reasonably inferable from the input. Do not invent \
  brand names, certifications, or specs that aren't implied by the text.
- If you cannot confidently determine a field, return an empty string for it.
- Respond with ONLY a JSON object, no other text, no code fences.
"""

USER_PROMPT_TEMPLATE = """Raw description: {desc}
Manufacturer (from supplier data, may be messy): {manuf}
Existing brand fields (already null if they were placeholders): \
E1_Brand={e1_brand}, Unilog_Brand={unilog_brand}, DIB_Brand={dib_brand}

Return JSON with exactly these keys:
{{
  "MANUFACTURER_NAME": "",
  "BRAND_NAME": "",
  "Classpath": "",
  "SHORT_DESC": "",
  "INVOICE_DESC": "",
  "MOBILE_DESC": "",
  "LONG_DESC1": "",
  "attributes": [{{"label": "", "value": "", "uom": ""}}]
}}
"""


def enrich_record(record: dict) -> dict:
    user_prompt = USER_PROMPT_TEMPLATE.format(
        desc=record.get("clean_description") or "",
        manuf=record.get("manufacturer_name_candidate") or record.get("part_manuf_raw") or "",
        e1_brand=record.get("e1_brand") or "",
        unilog_brand=record.get("unilog_brand") or "",
        dib_brand=record.get("dib_brand") or "",
    )

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )

    text = response.choices[0].message.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"MANUFACTURER_NAME": "", "BRAND_NAME": "", "Classpath": "",
                "SHORT_DESC": "", "INVOICE_DESC": "", "MOBILE_DESC": "",
                "LONG_DESC1": "", "attributes": []}