from typing import Any

SYSTEM_PROMPT = """Evaluate a student's answer choice for a multiple-choice question.

Return ONLY valid JSON with no markdown code fences or extra text.

JSON Schema:
{
  "is_correct": true/false,
  "misconception": "<short description of underlying misconception in Vietnamese, or null if correct>",
  "confidence": 0.95
}

Rules:
- Set is_correct to true if the selected option is correct, false otherwise.
- If is_correct is false, provide a brief description in Vietnamese explaining why the choice reflects a misconception. If correct, set misconception to null.
- Set confidence to a float between 0.0 and 1.0."""


def build_user_prompt(question: Any, selected_option_index: int) -> str:
    q_text = question.get("text") if isinstance(question, dict) else question.text
    options = question.get("options") if isinstance(question, dict) else question.options

    options_text = ""
    selected_option_text = ""
    for idx, opt in enumerate(options):
        opt_text = opt.get("text") if isinstance(opt, dict) else opt.text
        opt_correct = opt.get("is_correct") if isinstance(opt, dict) else opt.is_correct
        options_text += f"{idx}. {opt_text} {'(CORRECT OPTION)' if opt_correct else ''}\n"
        if idx == selected_option_index:
            selected_option_text = opt_text

    return f"""Question: {q_text}

Options:
{options_text}
Student selected option index {selected_option_index}: "{selected_option_text}"

Evaluate the answer and return JSON matching the schema."""
