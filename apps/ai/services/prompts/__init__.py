"""Package chứa các prompt module cho từng method của LLMService."""

from . import analyze_material
from . import chat_reply
from . import decide_next_action
from . import evaluate_answer
from . import generate_check_question
from . import generate_learning_path
from . import generate_lesson
from . import hint
from . import start_conversation

__all__ = [
    "analyze_material",
    "chat_reply",
    "decide_next_action",
    "evaluate_answer",
    "generate_check_question",
    "generate_learning_path",
    "generate_lesson",
    "hint",
    "start_conversation",
]
