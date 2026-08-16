from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


# ---------- Enums ----------

class ChatScope(str, Enum):
    ONBOARDING = "onboarding"
    MATERIAL = "material"
    GOAL = "goal"
    QUIZ = "quiz"


class ChatRole(str, Enum):
    STUDENT = "student"
    AI = "ai"


class QuestionPurpose(str, Enum):
    CHECKPOINT = "checkpoint"          # câu hỏi giữa/cuối chuỗi thẻ trong lesson
    LESSON_WRAPUP = "lesson_wrapup"    # bài luyện tập cuối lesson


class NextAction(str, Enum):
    EXPLAIN_AGAIN = "explain_again"
    SHOW_EXAMPLE = "show_example"
    PRACTICE_MORE = "practice_more"
    MOVE_NEXT = "move_next"


# ---------- Onboarding / Chat ----------

@dataclass
class ConversationResult:
    reply: str
    ready_to_analyze: bool = False
    detected_goal: Optional[str] = None


@dataclass
class ChatMessageDTO:
    role: ChatRole
    content: str


@dataclass
class LearningContextDTO:
    """Gửi kèm chat_reply để AI biết user đang ở đâu trong hành trình học."""
    current_goal: Optional[str] = None
    current_concept: Optional[str] = None
    current_lesson_order: Optional[int] = None
    current_lesson: Optional[str] = None


@dataclass
class ChatReplyResult:
    reply: str


# ---------- Material analysis ----------

@dataclass
class ConceptDTO:
    id: str
    title: str
    description: str = ""
    known_by_user: bool = False   # set sau khi qua Self-Check, dùng để lọc trước khi generate_learning_path


@dataclass
class AnalyzeMaterialResult:
    concepts: List[ConceptDTO]
    suggested_skills: List[str] = field(default_factory=list)


# ---------- Learning path (batch, forward-only) ----------

@dataclass
class LearningPathBatchResult:
    ordered_concept_ids: List[str]     # CHỈ thứ tự concept, KHÔNG chứa nội dung lesson
    is_final_batch: bool = False


# ---------- Lesson content (KHÔNG chứa câu hỏi) ----------

@dataclass
class FlashcardDTO:
    front: str
    back: str


@dataclass
class LessonCardDTO:
    order_index: int
    heading: str
    body: str


@dataclass
class LessonDTO:
    concept_id: str
    explanation: str
    example: str
    key_points: List[str]
    flashcards: List[FlashcardDTO]
    cards: List[LessonCardDTO]   # dạng thẻ next-next hiển thị trên UI


# ---------- Check question (dùng cho cả checkpoint và wrap-up) ----------

@dataclass
class QuestionOptionDTO:
    text: str
    is_correct: bool


@dataclass
class QuestionDTO:
    text: str
    options: List[QuestionOptionDTO]
    explanation: str
    purpose: QuestionPurpose = QuestionPurpose.CHECKPOINT
    after_card_order: Optional[int] = None


@dataclass
class CheckQuestionResult:
    questions: List[QuestionDTO]   # wrap-up có thể trả nhiều câu hơn checkpoint


# ---------- Answer evaluation ----------

@dataclass
class AnswerEvaluationResult:
    is_correct: bool
    misconception: Optional[str] = None   # mô tả ngắn hiểu sai kiểu gì, None nếu đúng
    confidence: float = 1.0               # 0.0-1.0, AI tự tin đánh giá này tới mức nào


# ---------- Next action decision ----------

@dataclass
class NextActionResult:
    action: NextAction
    concept_id: str
    reasoning: str = ""          # log nội bộ, KHÔNG hiển thị cho học sinh
    needs_next_batch: bool = False   # true khi action=MOVE_NEXT và đã hết batch hiện tại


# ---------- Hint ----------

@dataclass
class HintResult:
    level: int
    text: str