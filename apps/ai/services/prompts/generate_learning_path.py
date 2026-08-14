from typing import Any, List

SYSTEM_PROMPT = """Bạn là chuyên gia thiết kế chương trình học. Nhiệm vụ: từ danh sách các khái niệm (concepts)
và mức độ hiểu biết hiện tại của học sinh, hãy chọn và sắp xếp THỨ TỰ các concept_id cho đợt học tiếp theo (tối đa batch_size concept).

Lưu ý:
- KHÔNG sinh nội dung bài học hay bài tập.
- BẮT BUỘC trả về mảng ordered_concept_ids chứa các ID chuỗi (ví dụ: ["c1", "c2", "c3"]) trích xuất từ danh sách concept được cung cấp.

Trả JSON đúng format:
{
  "ordered_concept_ids": ["c1", "c2", "c3"],
  "is_final_batch": true/false
}

Quy tắc:
- ordered_concept_ids: mảng danh sách ID concept (chứa từ 1 đến batch_size ID lấy chính xác từ các ID được cung cấp).
- is_final_batch = true nếu đợt này đã bao gồm hết toàn bộ concept còn lại.
- Không thêm bất kỳ text nào ngoài JSON."""




def build_user_prompt(concepts: List[Any], mastery_context: dict, batch_size: int = 3) -> str:
    concepts_formatted = "\n".join(
        f"- ID: {c.get('id') if isinstance(c, dict) else c.id} | Title: {c.get('title') if isinstance(c, dict) else c.title} | Desc: {c.get('description', '') if isinstance(c, dict) else getattr(c, 'description', '')}"
        for c in concepts
    )
    return f"""Danh sách các concept cần sắp xếp lộ trình:
{concepts_formatted}

Bối cảnh năng lực/lịch sử học tập của học sinh (mastery_context):
{mastery_context}

Kích thước đợt học (batch_size): {batch_size}

Sắp xếp thứ tự học tối ưu và trả về JSON đúng format."""
