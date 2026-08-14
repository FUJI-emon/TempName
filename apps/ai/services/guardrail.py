"""
Guardrail: đảm bảo generate_hint không bao giờ lộ đáp án đúng.
Đây là lớp kiểm tra RUNTIME, chạy ngay sau khi LLM (fake hoặc adapter thật)
trả hint, TRƯỚC khi hint tới tay học sinh — không chỉ là test.
"""
import re

from .dto import QuestionDTO
from .exceptions import LLMInvalidResponseError


def _normalize(text: str) -> str:
    """Chuẩn hoá: lowercase, bỏ dấu câu/ký hiệu, gộp khoảng trắng thừa."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _significant_words(text: str) -> set:
    """Tập từ có nghĩa — bỏ từ 1 ký tự (v, f, λ...) vì quá ngắn để tính overlap,
    những đáp án dạng công thức ngắn được rule 1 (match nguyên văn) xử lý."""
    return {w for w in _normalize(text).split() if len(w) > 1}


def find_leaked_answer(hint_text: str, question: QuestionDTO, overlap_threshold: float = 0.75):
    """Trả về text đáp án đúng nếu hint bị nghi leak, None nếu an toàn."""
    norm_hint = _normalize(hint_text)
    hint_words = set(norm_hint.split())

    for option in question.options:
        if not option.is_correct:
            continue
        norm_answer = _normalize(option.text)
        if not norm_answer:
            continue

        # Rule 1: chép nguyên văn
        if norm_answer in norm_hint:
            return option.text

        # Rule 2: overlap từ vựng cao — chỉ áp dụng khi đáp án đủ dài
        # (>=3 từ có nghĩa) để tránh false positive với đáp án ngắn.
        answer_words = _significant_words(option.text)
        if len(answer_words) >= 3:
            overlap = len(answer_words & hint_words) / len(answer_words)
            if overlap >= overlap_threshold:
                return option.text

    return None


def assert_no_leak(hint_text: str, question: QuestionDTO) -> None:
    """Dùng trong pipeline thật: raise nếu phát hiện leak."""
    leaked = find_leaked_answer(hint_text, question)
    if leaked:
        raise LLMInvalidResponseError(
            f"Hint bị nghi leak đáp án (trùng nội dung với: {leaked!r})"
        )


def assert_no_leak_chat(reply_text: str, question: QuestionDTO = None) -> None:
    """Guardrail riêng cho chat_reply trong scope QUIZ để đảm bảo không bị lộ đáp án."""
    if question:
        leaked = find_leaked_answer(reply_text, question)
        if leaked:
            raise LLMInvalidResponseError(
                f"Chat reply bị nghi leak đáp án quiz (trùng nội dung với: {leaked!r})"
            )