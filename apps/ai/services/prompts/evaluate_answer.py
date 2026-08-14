from typing import Any

SYSTEM_PROMPT = """Bạn là trợ lý đánh giá bài làm của học sinh. Nhiệm vụ: đánh giá phương án lựa chọn
của học sinh cho một câu hỏi trắc nghiệm.

Yêu cầu:
- Xác định is_correct (true/false).
- Nếu sai (is_correct = false), hãy phân tích ngắn gọn lý do/bản chất hiểu sai (misconception) khiến học sinh chọn phương án đó. Nếu đúng, misconception là null.
- Đánh giá độ tự tin confidence (từ 0.0 đến 1.0).

Trả JSON đúng format:
{
  "is_correct": true/false,
  "misconception": "<mô tả ngắn về lỗi hiểu sai, hoặc null nếu đúng>",
  "confidence": 0.95
}
Không thêm bất kỳ text nào ngoài JSON."""


def build_user_prompt(question: Any, selected_option_index: int) -> str:
    q_text = question.get("text") if isinstance(question, dict) else question.text
    options = question.get("options") if isinstance(question, dict) else question.options

    options_text = ""
    selected_option_text = ""
    for idx, opt in enumerate(options):
        opt_text = opt.get("text") if isinstance(opt, dict) else opt.text
        opt_correct = opt.get("is_correct") if isinstance(opt, dict) else opt.is_correct
        options_text += f"{idx}. {opt_text} {'(ĐÁP ÁN ĐÚNG)' if opt_correct else ''}\n"
        if idx == selected_option_index:
            selected_option_text = opt_text

    return f"""Câu hỏi: {q_text}

Danh sách phương án:
{options_text}
Học sinh đã chọn phương án {selected_option_index}: "{selected_option_text}"

Đánh giá câu trả lời và trả về kết quả theo đúng format JSON."""
