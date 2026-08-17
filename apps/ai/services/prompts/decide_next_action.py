from typing import Any, List

SYSTEM_PROMPT = """You are an adaptive learning decision engine. Based on student answer evaluation history for the current concept, decide the next pedagogical action.

Return ONLY valid JSON with no markdown code fences or extra text.

JSON Schema:
{
  "action": "explain_again | show_example | practice_more | move_next",
  "concept_id": "<concept_id>",
  "reasoning": "<short rationale in English or Vietnamese>",
  "needs_next_batch": true/false
}

Action Criteria:
- "explain_again": Student repeated errors or fundamentally misunderstood concept.
- "show_example": Student struggled with applying formula/concept.
- "practice_more": Student partially correct but needs reinforcement.
- "move_next": Student demonstrated mastery. Set needs_next_batch to true if next concept batch is needed."""


def build_user_prompt(concept: Any, evaluation_history: List[Any]) -> str:
    concept_id = concept.get("id") if isinstance(concept, dict) else concept.id
    concept_title = concept.get("title") if isinstance(concept, dict) else concept.title

    history_str = ""
    for idx, eval_item in enumerate(evaluation_history):
        is_corr = eval_item.get("is_correct") if isinstance(eval_item, dict) else eval_item.is_correct
        misc = eval_item.get("misconception") if isinstance(eval_item, dict) else getattr(eval_item, "misconception", None)
        history_str += f"- Attempt {idx+1}: Correct={is_corr}, Misconception={misc}\n"

    if not evaluation_history:
        history_str = "No evaluation history."

    return f"""Current Concept: {concept_title} (ID: {concept_id})

Evaluation History:
{history_str}

Decide the next action and return JSON matching the schema."""
