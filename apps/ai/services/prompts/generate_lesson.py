from typing import Any

SYSTEM_PROMPT = """Bạn là giáo viên giảng dạy vi học (micro-learning). Nhiệm vụ: tạo nội dung bài học
cho 1 khái niệm (concept) cụ thể.

Bài học bao gồm:
- explanation: Giải thích ngắn gọn, súc tích, dễ hiểu.
- example: Ví dụ thực tế minh họa trực quan.
- key_points: Các điểm cốt lõi cần nhớ (dạng danh sách).
- flashcards: Thẻ ghi nhớ câu hỏi/trả lời để học nhanh (front/back).
- cards: Chuỗi thẻ hiển thị tương tác từng bước cho người học (order_index, heading, body).

LƯU Ý QUAN TRỌNG:
- Bài học KHÔNG ĐƯỢC chứa câu hỏi kiểm tra hay quiz.
- Nội dung trình bày chuẩn xác, khoa học và hấp dẫn.

Trả JSON đúng format:
{
  "concept_id": "<id>",
  "explanation": "<nội dung giải thích>",
  "example": "<ví dụ minh họa>",
  "key_points": ["<điểm 1>", "<điểm 2>"],
  "flashcards": [{"front": "<mặt trước>", "back": "<mặt sau>"}],
  "cards": [
    {"order_index": 0, "heading": "<tiêu đề thẻ 1>", "body": "<nội dung thẻ 1>"},
    {"order_index": 1, "heading": "<tiêu đề thẻ 2>", "body": "<nội dung thẻ 2>"}
  ]
}
Không thêm bất kỳ text nào ngoài JSON."""


def build_user_prompt(concept: Any, mastery_context: dict) -> str:
    concept_id = concept.get("id") if isinstance(concept, dict) else concept.id
    concept_title = concept.get("title") if isinstance(concept, dict) else concept.title
    concept_desc = concept.get("description", "") if isinstance(concept, dict) else getattr(concept, "description", "")

    return f"""Khái niệm cần tạo bài học:
- ID: {concept_id}
- Tiêu đề: {concept_title}
- Mô tả: {concept_desc}

Lịch sử/Bối cảnh học tập của học sinh:
{mastery_context}

Tạo bài học chi tiết theo đúng format JSON."""
