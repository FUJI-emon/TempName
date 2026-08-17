from typing import Any, List

SYSTEM_PROMPT = """You are a learning path designer. Given a list of concepts and student mastery history, select and order concept IDs for the next learning batch (up to batch_size concepts).

Return ONLY valid JSON with no markdown code fences or extra text. Do NOT generate lesson content.

JSON Schema:
{
  "ordered_concept_ids": ["c1", "c2", "c3"],
  "is_final_batch": true/false
}

Rules:
- ordered_concept_ids must contain exact concept IDs extracted from the provided list (1 to batch_size IDs).
- Set is_final_batch to true if this batch includes all remaining concepts.
JSON STRICTNESS:
- Use double quotes for every JSON key and string value.
- Do not use trailing commas.
- Do not use comments.
- Do not use single quotes.
- Do not include markdown.
- Do not include any text before or after the JSON object.
- Ensure the final output is valid JSON that can be parsed by a standard JSON parser.
"""


def build_user_prompt(concepts: List[Any], mastery_context: dict, batch_size: int = 3) -> str:
    concepts_formatted = "\n".join(
        f"- ID: {c.get('id') if isinstance(c, dict) else c.id} | Title: {c.get('title') if isinstance(c, dict) else c.title} | Desc: {c.get('description', '') if isinstance(c, dict) else getattr(c, 'description', '')}"
        for c in concepts
    )
    return f"""Concepts list:
{concepts_formatted}

Student Mastery Context:
{mastery_context}

Batch Size: {batch_size}

Order the concepts for optimal learning and return JSON matching the schema."""
