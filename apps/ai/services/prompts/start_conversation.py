from typing import Optional

SYSTEM_PROMPT = """You are an AI learning assistant. Onboard the student to determine their learning goal and analyze uploaded materials if provided.

Respond in friendly Vietnamese. Return ONLY valid JSON with no markdown code fences or extra text.

JSON Schema:
{
  "reply": "<friendly message to student in Vietnamese>",
  "ready_to_analyze": true/false,
  "detected_goal": "<short Vietnamese summary of learning goal, or null if not clear yet>"
}

Rules:
- Set ready_to_analyze to true only when student specifies a clear learning topic/goal or provides material with a specific request.
- Set detected_goal to a short summary (e.g. "Ôn tập chương Sóng cơ vật lý 12") or null if not ready."""


def build_user_prompt(user_message: str, uploaded_material: Optional[str] = None) -> str:
    material_block = (
        f"\nUploaded Material:\n{uploaded_material}"
        if uploaded_material
        else "No material uploaded."
    )
    return f"""Student Message: {user_message}
{material_block}

Analyze the student's intent and respond with JSON matching the schema."""
