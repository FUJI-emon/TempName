from abc import ABC, abstractmethod
from typing import List, Optional

from .dto import (
    AnalyzeMaterialResult, AnswerEvaluationResult, ChatMessageDTO,
    ChatReplyResult, ChatScope, CheckQuestionResult, ConceptDTO,
    ConversationResult, HintResult, LearningContextDTO,
    LearningPathBatchResult, LessonDTO, NextActionResult,
    QuestionDTO, QuestionPurpose,
)


class LLMService(ABC):
    """
    Interface duy nhất mà toàn bộ app được phép gọi để tương tác AI.
    Luôn lấy instance qua factory.get_llm_service().
    """

    @abstractmethod
    def start_conversation(
        self, user_message: str, uploaded_material: Optional[str] = None
    ) -> ConversationResult:
        """Mở đầu: xác định mục tiêu học, có thể kèm tài liệu."""
        raise NotImplementedError

    @abstractmethod
    def analyze_material(self, material_content: str, goal: str) -> AnalyzeMaterialResult:
        """Tài liệu + mục tiêu -> danh sách concept cần học."""
        raise NotImplementedError

    @abstractmethod
    def generate_learning_path(
        self,
        concepts: List[ConceptDTO],   # đã lọc known_by_user=True sau Self-Check
        mastery_context: dict,
        batch_size: int = 3,
    ) -> LearningPathBatchResult:
        """
        Sinh THỨ TỰ đợt kế tiếp (mặc định 3 concept), KHÔNG sinh nội
        dung lesson. Đợt sau thay thế đợt trước — path forward-only,
        không giữ lại để duyệt lại toàn bộ.
        """
        raise NotImplementedError

    @abstractmethod
    def generate_lesson(
        self,
        concept: ConceptDTO,
        mastery_context: dict,
        goal_context: Optional[dict] = None,
        material_context: Optional[str] = None,
    ) -> LessonDTO:
        """
        Nội dung học của 1 concept: explanation, example, key_points,
        flashcards, cards (thẻ next-next). KHÔNG chứa câu hỏi.
        """
        raise NotImplementedError

    @abstractmethod
    def generate_check_question(
        self,
        concept: ConceptDTO,
        lesson: LessonDTO,
        purpose: QuestionPurpose,
        previous_misconceptions: Optional[List[str]] = None,
    ) -> CheckQuestionResult:
        """
        purpose=CHECKPOINT: 1 câu hỏi giữa/cuối chuỗi thẻ.
        purpose=LESSON_WRAPUP: bài luyện tập cuối lesson (có thể nhiều câu hơn).
        previous_misconceptions: nếu có (từ lần EXPLAIN_AGAIN trước), AI
        nên ra câu hỏi nhắm đúng vào điểm hiểu sai đó.
        """
        raise NotImplementedError

    @abstractmethod
    def evaluate_answer(
        self, question: QuestionDTO, selected_option_index: int
    ) -> AnswerEvaluationResult:
        """Đánh giá đúng/sai + phát hiện misconception nếu sai."""
        raise NotImplementedError

    @abstractmethod
    def decide_next_action(
        self, concept: ConceptDTO, evaluation_history: List[AnswerEvaluationResult]
    ) -> NextActionResult:
        """
        Bước Adapt: dựa trên lịch sử evaluate_answer của concept hiện tại
        -> EXPLAIN_AGAIN / SHOW_EXAMPLE / PRACTICE_MORE / MOVE_NEXT.
        """
        raise NotImplementedError

    @abstractmethod
    def generate_hint(
        self, question: QuestionDTO, level: int, previous_hints: List[str]
    ) -> HintResult:
        """
        3 cấp, dùng chung cho checkpoint và wrap-up. Không bao giờ trả
        đáp án trực tiếp.
        """
        raise NotImplementedError

    @abstractmethod
    def chat_reply(
        self,
        history: List[ChatMessageDTO],
        new_message: str,
        scope: ChatScope,
        learning_context: Optional[LearningContextDTO] = None,
    ) -> ChatReplyResult:
        """
        scope=QUIZ: guardrail chặt, không lộ đáp án dù hỏi vòng vo.
        learning_context giúp AI biết user đang học goal/concept nào.
        """
        raise NotImplementedError