from typing import Any, Optional

SYSTEM_PROMPT = """You are an expert micro-learning teacher. Generate lesson content for a specific concept.

Return ONLY valid JSON with no markdown code fences or extra text.

JSON Schema:
{
  "concept_id": "<concept_id>",
  "explanation": "<concise summary explanation in Vietnamese>",
  "example": "<practical illustrative example in Vietnamese>",
  "key_points": ["<key takeaway 1>", "<key takeaway 2>"],
  "flashcards": [
    {
      "front": "<question/term in Vietnamese>",
      "back": "<answer/definition in Vietnamese>"
    }
  ],
  "cards": [
    {
      "order_index": 1,
      "heading": "<card title in Vietnamese>",
      "body": "<card lesson content in Vietnamese>"
    }
  ]
}

Rules:
- Generate 2 to 4 interactive cards depending on concept complexity.
- Card order_index must start at 1 (1, 2, 3...).
- All card bodies must contain actual teaching content in Vietnamese.
- Do NOT include questions, quizzes, or checkpoints inside cards or lesson content."""


def build_user_prompt(
    concept: Any,
    mastery_context: dict,
    goal_context: Optional[dict] = None,
    material_context: Optional[str] = None,
) -> str:
    concept_id = concept.get("id") if isinstance(concept, dict) else concept.id
    concept_title = concept.get("title") if isinstance(concept, dict) else concept.title
    concept_desc = concept.get("description", "") if isinstance(concept, dict) else getattr(concept, "description", "")

    goal_title = goal_context.get("title", "") if goal_context else ""
    goal_desc = goal_context.get("description", "") if goal_context else ""

    mat_text = f"\nExtracted Material Context:\n{material_context[:1000]}" if material_context else ""

    return f"""Target Learning Goal:
- Title: {goal_title}
- Description: {goal_desc}

Concept to teach:
- ID: {concept_id}
- Title: {concept_title}
- Description: {concept_desc}
{mat_text}

Student Mastery Context:
{mastery_context}

Generate the micro-learning lesson and return JSON matching the schema."""
