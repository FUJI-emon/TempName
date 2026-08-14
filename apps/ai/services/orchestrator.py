from dataclasses import dataclass
from typing import List, Optional

from .dto import (
    AnswerEvaluationResult,
    ConceptDTO,
    LessonDTO,
    NextAction,
    NextActionResult,
    QuestionPurpose,
)
from .factory import get_llm_service
from .guardrail import assert_no_leak
from .exceptions import LLMInvalidResponseError


@dataclass
class LessonSessionState:
    """State tạm trong 1 phiên học 1 concept — giữ ở cache/session,
    KHÔNG phải Django model (đó là việc của A ghi progress cuối cùng)."""

    concept: ConceptDTO
    lesson: LessonDTO
    evaluation_history: List[AnswerEvaluationResult]


class LearningOrchestrator:
    """
    Điều phối vòng lặp Learn -> Measure -> Adapt.
    View trong apps/quiz và apps/progress gọi các method của class này,
    KHÔNG gọi thẳng LLMService.
    """

    def __init__(self, llm_service=None):
        self.llm = llm_service or get_llm_service()

    def start_new_path_batch(self, concepts: List[ConceptDTO], mastery_context: dict):
        """Sinh đợt 3 concept tiếp theo."""
        return self.llm.generate_learning_path(concepts, mastery_context, batch_size=3)

    def start_lesson(
        self, concept: ConceptDTO, mastery_context: dict
    ) -> LessonSessionState:
        lesson = self.llm.generate_lesson(concept, mastery_context)
        return LessonSessionState(concept=concept, lesson=lesson, evaluation_history=[])

    def get_checkpoint_question(self, session: LessonSessionState):
        result = self.llm.generate_check_question(
            session.concept, session.lesson, purpose=QuestionPurpose.CHECKPOINT
        )
        return result.questions[0]

    def submit_checkpoint_answer(
        self, session: LessonSessionState, question, selected_option_index: int
    ) -> NextActionResult:
        evaluation = self.llm.evaluate_answer(question, selected_option_index)
        session.evaluation_history.append(evaluation)
        return self.llm.decide_next_action(session.concept, session.evaluation_history)

    def handle_next_action(
        self, session: LessonSessionState, decision: NextActionResult
    ):
        if decision.action == NextAction.EXPLAIN_AGAIN:
            misconceptions = [
                e.misconception for e in session.evaluation_history if e.misconception
            ]
            session.lesson = self.llm.generate_lesson(
                session.concept, {"previous_misconceptions": misconceptions}
            )
            return session.lesson
        elif decision.action == NextAction.SHOW_EXAMPLE:
            return session.lesson.example
        elif decision.action == NextAction.PRACTICE_MORE:
            return self.get_checkpoint_question(session)
        elif decision.action == NextAction.MOVE_NEXT:
            return self.get_lesson_wrapup_test(session)

    def get_lesson_wrapup_test(self, session: LessonSessionState):
        """Final test cuối MỖI lesson."""
        return self.llm.generate_check_question(
            session.concept, session.lesson, purpose=QuestionPurpose.LESSON_WRAPUP
        )

    def submit_wrapup_answers(
        self, session: LessonSessionState, answers: list
    ) -> NextActionResult:
        for question, selected_index in answers:
            evaluation = self.llm.evaluate_answer(question, selected_index)
            session.evaluation_history.append(evaluation)

        decision = self.llm.decide_next_action(
            session.concept, session.evaluation_history
        )
        return decision

    def get_hint(self, question, level: int, previous_hints: list):
        """
        Sinh hint cho checkpoint question, có guardrail chặn leak đáp án.
        Thử lại 1 lần nếu leak; nếu lần 2 vẫn leak thì raise để view fallback
        (vd: hiển thị hint level trước đó, hoặc thông báo lỗi cho học sinh).
        """
        hint = self.llm.generate_hint(question, level, previous_hints)
        try:
            assert_no_leak(hint.text, question)
        except LLMInvalidResponseError:
            hint = self.llm.generate_hint(question, level, previous_hints)
            assert_no_leak(hint.text, question)  # lần 2 vẫn leak thì bay lên trên
        return hint
