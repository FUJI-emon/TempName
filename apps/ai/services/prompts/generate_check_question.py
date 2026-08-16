from typing import Any, List, Optional

SYSTEM_PROMPT = """Bạn là chuyên gia soạn đề thi trắc nghiệm đánh giá năng lực. Nhiệm vụ: tạo câu hỏi
kiểm tra độ hiểu cho khái niệm (concept) và bài học (lesson) vừa học.

Yêu cầu:
- purpose = "checkpoint": Sinh 1 câu hỏi trắc nghiệm kiểm tra nhanh.
- purpose = "lesson_wrapup": Sinh bài luyện tập tổng hợp (2-3 câu hỏi trắc nghiệm).
- Nếu có previous_misconceptions (các điểm học sinh từng hiểu sai), hãy thiết kế câu hỏi nhắm trực tiếp vào việc kiểm tra khắc phục các lỗi sai đó.
- Mỗi câu hỏi trắc nghiệm có 3-4 phương án, đúng duy nhất 1 phương án (is_correct: true).

Trả JSON đúng format:
{
  "questions": [
    {
      "text": "<nội dung câu hỏi>",
      "options": [
        {"text": "<phương án A>", "is_correct": true},
        {"text": "<phương án B>", "is_correct": false},
        {"text": "<phương án C>", "is_correct": false}
      ],
      "explanation": "<lời giải thích chi tiết đáp án>",
      "purpose": "checkpoint"
    }
  ]
}
Không thêm bất kỳ text nào ngoài JSON."""


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
            heading = c.heading if hasattr(c, "heading") else c.get("heading", "")
            body = c.body if hasattr(c, "body") else c.get("body", "")
            card_items.append(f"  + Thẻ {idx+1} [{heading}]: {body}")
        cards_text = "\nNội dung các thẻ bài học đã giảng dạy:\n" + "\n".join(card_items)

    misconceptions_block = (
        "\nCác điểm hiểu sai trước đó cần kiểm tra lại:\n" + "\n".join(f"- {m}" for m in previous_misconceptions)
        if previous_misconceptions
        else "Chưa có ghi nhận hiểu sai trước đó."
    )

    return f"""Khái niệm: {concept_title}
Bài học tóm tắt: {lesson_exp}
{cards_text}
Mục đích câu hỏi (purpose): {purpose_val}
{misconceptions_block}

Dựa TRỰC TIẾP vào nội dung các thẻ bài học trên, tạo các câu hỏi trắc nghiệm kiểm tra tương ứng theo đúng format JSON."""
