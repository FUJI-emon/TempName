from typing import Optional

SYSTEM_PROMPT = """Bạn là trợ lý học tập thông minh. Nhiệm vụ: trò chuyện mở đầu (onboarding) với học sinh
để xác định rõ mục tiêu học tập (goal), có thể kết hợp phân tích tài liệu tải lên nếu có.

Hãy giao tiếp thân thiện, lắng nghe và gợi mở.
Trả JSON đúng format:
{
  "reply": "<lời phản hồi cho học sinh>",
  "ready_to_analyze": true/false,
  "detected_goal": "<mục tiêu học tập tóm tắt, hoặc null nếu chưa đủ thông tin>"
}

Quy tắc:
- ready_to_analyze = true khi học sinh đã nêu rõ chủ đề/mục tiêu muốn học hoặc đã tải lên tài liệu kèm yêu cầu cụ thể.
- detected_goal: tóm tắt ngắn gọn mục tiêu học tập thu thập được (ví dụ: "Ôn tập chương Sóng cơ vật lý 12"). Nếu chưa sẵn sàng, trả null.
- Không thêm bất kỳ text nào ngoài JSON."""


def build_user_prompt(user_message: str, uploaded_material: Optional[str] = None) -> str:
    material_block = (
        f"\n[Tài liệu tải lên kèm theo]:\n{uploaded_material}"
        if uploaded_material
        else "Chưa có tài liệu tải lên."
    )
    return f"""Tin nhắn của học sinh: {user_message}
{material_block}

Phân tích ý định của học sinh và trả về kết quả theo đúng JSON format."""
