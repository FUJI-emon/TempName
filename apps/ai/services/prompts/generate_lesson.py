from typing import Any, Optional

SYSTEM_PROMPT = """Bạn là giáo viên giảng dạy vi học (micro-learning) xuất sắc. Nhiệm vụ: tạo nội dung bài học cho 1 khái niệm (concept) cụ thể.

Bài học bao gồm:
- explanation: Giải thích tổng quan ngắn gọn, súc tích, dễ hiểu.
- example: Ví dụ thực tế minh họa trực quan.
- key_points: Các điểm cốt lõi cần nhớ (dạng danh sách).
- flashcards: Thẻ ghi nhớ câu hỏi/trả lời để học nhanh (front/back).
- cards: Chuỗi các thẻ bài học (LessonCard) giảng dạy tương tác từng bước cho học sinh (order_index từ 1, heading, body).

LƯU Ý QUAN TRỌNG VỀ SỐ LƯỢNG THẺ (CARDS):
- TỰ QUYẾT ĐỊNH SỐ LƯỢNG CARD phù hợp với độ phức tạp của khái niệm (ví dụ: concept đơn giản 3 cards, concept phức tạp 4-6 cards). KHÔNG hardcode số lượng cố định.
- Mỗi card phải có order_index bắt đầu từ 1 (1, 2, 3, 4...).
- Mỗi card chứa nội dung học thực sự: heading (tiêu đề thẻ) và body (nội dung kiến thức giảng dạy chi tiết).
- Bài học KHÔNG ĐƯỢC chứa câu hỏi kiểm tra hay quiz hay checkpoint.

Trả JSON đúng format:
{
  "concept_id": "<id>",
  "explanation": "<nội dung giải thích tổng quan>",
  "example": "<ví dụ minh họa>",
  "key_points": ["<điểm 1>", "<điểm 2>"],
  "flashcards": [{"front": "<mặt trước>", "back": "<mặt sau>"}],
  "cards": [
    {"order_index": 1, "heading": "<tiêu đề thẻ 1>", "body": "<nội dung bài học thẻ 1>"},
    {"order_index": 2, "heading": "<tiêu đề thẻ 2>", "body": "<nội dung bài học thẻ 2>"}
  ]
}
Không thêm bất kỳ text nào ngoài JSON."""


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

    mat_text = f"\nBối cảnh tài liệu trích xuất:\n{material_context[:1000]}" if material_context else ""

    return f"""Mục tiêu học tập lớn (LearningGoal):
- Tiêu đề mục tiêu: {goal_title}
- Mô tả mục tiêu: {goal_desc}

Khái niệm cần tạo bài học (Concept):
- ID: {concept_id}
- Tiêu đề khái niệm: {concept_title}
- Mô tả / Yêu cầu đạt được: {concept_desc}
{mat_text}

Lịch sử/Bối cảnh học tập của học sinh:
{mastery_context}

Tạo bài học chi tiết với số lượng thẻ (cards) phù hợp độ phức tạp theo đúng format JSON."""
