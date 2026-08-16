from typing import Any, List, Optional

SYSTEM_PROMPT = """Bạn là chuyên gia soạn đề thi trắc nghiệm đánh giá năng lực. Nhiệm vụ: tạo câu hỏi kiểm tra độ hiểu cho bài học vừa tạo.

Yêu cầu theo purpose:
1. Khi purpose = "checkpoint":
   - Tạo câu hỏi kiểm tra ngắt chặng (Checkpoint Questions) chèn giữa các thẻ bài học.
   - SỐ LƯỢNG CHECKPOINT KHÔNG CỐ ĐỊNH, AI tự quyết định dựa trên các kiến thức trọng tâm cần kiểm tra.
   - MỖI CÂU HỎI CHECKPOINT BẮT BUỘC có field `after_card_order` xác định vị trí xuất hiện (dạng 1-based, ví dụ: `after_card_order = 2` nghĩa là hiển thị ngay sau Thẻ 2).
   - KHÔNG ĐƯỢC kiểm tra kiến thức chưa được học (câu hỏi tại after_card_order = N chỉ được kiểm tra nội dung từ Thẻ 1 đến Thẻ N).

2. Khi purpose = "lesson_wrapup":
   - Tạo bài thi Final Exam đánh giá kiến thức tổng thể của TOÀN BỘ bài học.
   - Đặt `after_card_order` là null (None).

Yêu cầu chung:
- Mỗi câu hỏi trắc nghiệm có 3-4 phương án, đúng duy nhất 1 phương án (is_correct: true).
- Có lời giải thích (explanation) chi tiết cho câu hỏi.

Trả JSON đúng format:
{
  "questions": [
    {
      "text": "<nội dung câu hỏi>",
      "after_card_order": 2,
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
            order = getattr(c, "order_index", idx + 1) if not isinstance(c, dict) else c.get("order_index", idx + 1)
            heading = getattr(c, "heading", "") if not isinstance(c, dict) else c.get("heading", "")
            body = getattr(c, "body", "") if not isinstance(c, dict) else c.get("body", "")
            card_items.append(f"  + Thẻ {order} [{heading}]: {body}")
        cards_text = "\nNội dung các thẻ bài học (1-based order):\n" + "\n".join(card_items)

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

Dựa TRỰC TIẾP vào nội dung các thẻ bài học trên, tạo các câu hỏi trắc nghiệm tương ứng theo đúng format JSON."""
