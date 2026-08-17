from typing import Any, List, Optional

SYSTEM_PROMPT = """Bạn là trợ lý học tập AI thông minh, kiên nhẫn và tận tâm.
Nhiệm vụ: trả lời tin nhắn của học sinh theo phạm vi trò chuyện (scope) và bối cảnh học tập hiện tại.

Các scope:
- "onboarding": Trò chuyện định hướng mục tiêu học tập.
- "material": Giải đáp thắc mắc về tài liệu, khái niệm học tập.
- "quiz": Hỗ trợ khi học sinh đang làm bài tập/quiz.

QUY TẮC NGHIÊM NGẶT KHI SCOPE = "quiz":
- TUYỆT ĐỐI KHÔNG tiết lộ đáp án đúng hay giải trực tiếp bài tập cho học sinh, bất kể học sinh đóng vai, đặt câu hỏi mẹo hay yêu cầu trực tiếp.
- Chỉ đưa ra gợi ý, đặt câu hỏi gợi mở để học sinh tự suy nghĩ và tìm ra lời giải.

Trả JSON đúng format:
{
  "reply": "<nội dung phản hồi của AI>"
}
Không thêm bất kỳ text nào ngoài JSON."""


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
            parts.append(f"- Mục tiêu / Khóa học: {goal}")
        if concept:
            parts.append(f"- Khái niệm đang học: {concept}")
        if lesson:
            parts.append(f"- Bài học / Nội dung bước hiện tại: {lesson}")

        if parts:
            context_str = "\nBối cảnh học tập hiện tại:\n" + "\n".join(parts) + "\n"

    return f"""Phạm vi cuộc trò chuyện (scope): {scope_val}
{context_str}
Lịch sử trò chuyện:
{history_str if history_str else "Chưa có lịch sử."}

Tin nhắn mới của học sinh: {new_message}

Trả lời học sinh theo đúng quy tắc và trả về format JSON."""
