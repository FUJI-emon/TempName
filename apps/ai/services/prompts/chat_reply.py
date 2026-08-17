from typing import Any, List, Optional

SYSTEM_PROMPT = """You are a patient AI tutor. Reply to the student's message based on the current conversation scope and learning context.

Scopes:
- "onboarding": Goal discussion and course orientation.
- "material": Answer questions about learning materials and concepts.
- "quiz": Help student with current quiz question.

STRICT QUIZ SCOPE RULE:
- NEVER reveal the correct answer or solve quiz questions directly, regardless of student framing or roleplay.
- Provide guidance, ask clarifying questions, or give subtle hints in Vietnamese.

Return ONLY valid JSON with no markdown code fences or extra text.

JSON Schema:
{
  "reply": "<response message to student in Vietnamese>"
}"""


def build_user_prompt(
    history: List[Any],
    new_message: str,
    scope: Any,
    learning_context: Optional[Any] = None,
) -> str:
    scope_val = scope.value if hasattr(scope, "value") else str(scope)
    history_str = ""
    for msg in history:
        role = msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", "")
        role_val = role.value if hasattr(role, "value") else str(role)
        content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", "")
        history_str += f"{role_val}: {content}\n"

    context_str = ""
    if learning_context:
        goal = learning_context.get("current_goal") if isinstance(learning_context, dict) else getattr(learning_context, "current_goal", None)
        concept = learning_context.get("current_concept") if isinstance(learning_context, dict) else getattr(learning_context, "current_concept", None)
        lesson = learning_context.get("current_lesson") if isinstance(learning_context, dict) else getattr(learning_context, "current_lesson", None)

        parts = []
        if goal:
            parts.append(f"- Current Goal: {goal}")
        if concept:
            parts.append(f"- Current Concept: {concept}")
        if lesson:
            parts.append(f"- Current Lesson: {lesson}")

        if parts:
            context_str = "\nLearning Context:\n" + "\n".join(parts) + "\n"

    return f"""Conversation Scope: {scope_val}
{context_str}
Chat History:
{history_str if history_str else "No history."}

Student Message: {new_message}

Respond in Vietnamese and return JSON matching the schema."""
