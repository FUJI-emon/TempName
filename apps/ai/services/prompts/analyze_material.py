SYSTEM_PROMPT = """Analyze the provided learning material and target goal. Extract key learning concepts required to achieve the goal.

Return ONLY valid JSON with no markdown code fences or extra text.

JSON Schema:
{
  "concepts": [
    {
      "id": "c1",
      "title": "<concept title in Vietnamese>",
      "description": "<brief description in Vietnamese>"
    }
  ],
  "suggested_skills": ["<skill 1 in Vietnamese>"]
}

Rules:
- Concept IDs must be sequentially formatted as c1, c2, c3...
- Keep concept titles and descriptions clear, concise, and in Vietnamese."""


def build_user_prompt(material_content: str, goal: str) -> str:
    return f"""Learning Material:
{material_content}

Target Goal:
{goal}

Extract concepts and return JSON matching the schema."""