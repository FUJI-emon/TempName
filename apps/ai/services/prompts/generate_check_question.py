from typing import Any, List, Optional

SYSTEM_PROMPT = """You are a test item writer. Generate multiple-choice assessment questions for a lesson.

Return ONLY valid JSON with no markdown code fences or extra text.

JSON Schema:
{
  "questions": [
    {
      "text": "<question text in Vietnamese>",
      "after_card_order": 1,
      "options": [
        {"text": "<option A in Vietnamese>", "is_correct": true},
        {"text": "<option B in Vietnamese>", "is_correct": false},
        {"text": "<option C in Vietnamese>", "is_correct": false}
      ],
      "explanation": "<detailed explanation in Vietnamese>",
      "purpose": "checkpoint"
    }
  ]
}

Rules:
- When purpose is "checkpoint": generate 1 to 2 short check questions. Set after_card_order to a 1-based card index (e.g. 1, 2). Only test material covered up to that card index.
- When purpose is "lesson_wrapup": generate exactly 2 final exam questions assessing the entire lesson. Set after_card_order to null.
- Provide exactly 3  options per question with exactly one option having is_correct set to true."""


def build_user_prompt(
    concept: Any,
    lesson: Any,
    purpose: Any,
    previous_misconceptions: Optional[List[str]] = None,
) -> str:
    concept_title = concept.get("title") if isinstance(concept, dict) else concept.title
    lesson_exp = lesson.get("explanation") if isinstance(lesson, dict) else getattr(lesson, "explanation", "")
    purpose_val = purpose.value if hasattr(purpose, "value") else str(purpose)

    cards_list = getattr(lesson, "cards", []) if not isinstance(lesson, dict) else lesson.get("cards", [])
    cards_text = ""
    if cards_list:
        card_items = []
        for idx, c in enumerate(cards_list):
            order = getattr(c, "order_index", idx + 1) if not isinstance(c, dict) else c.get("order_index", idx + 1)
            heading = getattr(c, "heading", "") if not isinstance(c, dict) else c.get("heading", "")
            body = getattr(c, "body", "") if not isinstance(c, dict) else c.get("body", "")
            card_items.append(f"  + Card {order} [{heading}]: {body}")
        cards_text = "\nLesson Cards (1-based order):\n" + "\n".join(card_items)

    misconceptions_block = (
        "\nTarget previous misconceptions:\n" + "\n".join(f"- {m}" for m in previous_misconceptions)
        if previous_misconceptions
        else "No previous misconceptions recorded."
    )

    return f"""Concept: {concept_title}
Lesson Summary: {lesson_exp}
{cards_text}
Purpose: {purpose_val}
{misconceptions_block}

Generate questions based directly on the lesson cards and return JSON matching the schema."""
