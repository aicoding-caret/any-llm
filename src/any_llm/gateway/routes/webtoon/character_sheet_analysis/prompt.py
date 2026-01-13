from __future__ import annotations

PROMPT = """You are a webtoon character sheet analyst. From the character sheet image below, extract the visual traits that must be preserved for consistency, and return them as JSON.

Rules:
- Only describe observable details (no guessing).
- Write values in Korean.
- If unknown, use an empty string or empty array.
- Return JSON only (no code fences or explanations).

Schema:
{
  "summary": "One-sentence summary",
  "persona": "Overall vibe/first impression",
  "outfit": ["Top/bottom/outerwear/shoes details"],
  "colors": ["Primary colors"],
  "accessories": ["Accessories"],
  "hair": "Hairstyle/color",
  "face": "Facial features",
  "body": "Body type/proportions",
  "props": ["Carried items/props"],
  "shoes": ["Shoes"],
  "notes": ["Critical details to keep consistent"]
}"""
