from typing import Any, List

SYSTEM_PROMPT = """Bạn là hệ thống học tập thích ứng (Adaptive Learning System). Nhiệm vụ: dựa vào lịch sử
đánh giá câu trả lời của học sinh đối với concept hiện tại để quyết định bước đi tiếp theo (next action).

Các hành động khả thi (action):
- "explain_again": Giảng lại khái niệm theo cách tiếp cận mới (khi học sinh làm sai nhiều hoặc hiểu sai căn bản).
- "show_example": Đưa thêm ví dụ trực quan minh họa (khi học sinh chưa nắm chắc cách áp dụng).
- "practice_more": Cho làm thêm bài tập cùng cấp độ (khi học sinh làm đúng một phần nhưng cần củng cố).
- "move_next": Chuyển sang concept tiếp theo (khi học sinh đã đạt mức độ thành thạo/mastery).

Trả JSON đúng format:
{
  "action": "explain_again | show_example | practice_more | move_next",
  "concept_id": "<id>",
  "reasoning": "<lý do đưa ra quyết định>",
  "needs_next_batch": true/false
}

Quy tắc:
- reasoning: Giải thích logic đằng sau quyết định (dành cho log hệ thống).
- needs_next_batch: set true nếu action="move_next" và cần tải đợt concept tiếp theo.
- Không thêm bất kỳ text nào ngoài JSON."""


def build_user_prompt(concept: Any, evaluation_history: List[Any]) -> str:
    concept_id = concept.get("id") if isinstance(concept, dict) else concept.id
    concept_title = concept.get("title") if isinstance(concept, dict) else concept.title

    history_str = ""
    for idx, eval_item in enumerate(evaluation_history):
        is_corr = eval_item.get("is_correct") if isinstance(eval_item, dict) else eval_item.is_correct
        misc = eval_item.get("misconception") if isinstance(eval_item, dict) else getattr(eval_item, "misconception", None)
        history_str += f"- Lần {idx+1}: Correct={is_corr}, Misconception={misc}\n"

    if not evaluation_history:
        history_str = "Chưa có lịch sử làm bài cho concept này."

    return f"""Concept hiện tại: {concept_title} (ID: {concept_id})

Lịch sử trả lời của học sinh:
{history_str}

Quyết định bước tiếp theo và trả về đúng format JSON."""
