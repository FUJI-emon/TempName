from typing import List, Optional

from .dto import (
    AnalyzeMaterialResult,
    AnswerEvaluationResult,
    ChatMessageDTO,
    ChatReplyResult,
    ChatScope,
    CheckQuestionResult,
    ConceptDTO,
    ConversationResult,
    FlashcardDTO,
    HintResult,
    LearningContextDTO,
    LearningPathBatchResult,
    LessonCardDTO,
    LessonDTO,
    NextAction,
    NextActionResult,
    QuestionDTO,
    QuestionOptionDTO,
    QuestionPurpose,
)
from .interface import LLMService
from .exceptions import LLMEmptyInputError


class FakeLLMService(LLMService):
    """Bản giả — dùng trong unit test của quiz/progress/chat, không gọi AI thật."""

    def start_conversation(self, user_message, uploaded_material=None):
        return ConversationResult(
            reply="Chào bạn! Bạn muốn học chủ đề gì hôm nay?",
            ready_to_analyze=uploaded_material is not None,
            detected_goal="Ôn tập chương Sóng" if uploaded_material else None,
        )

    def analyze_material(self, material_content, goal):
        if not material_content or not material_content.strip():
            raise LLMEmptyInputError("material_content không được để trống")

        return AnalyzeMaterialResult(
            concepts=[
                ConceptDTO(id="c1", title="Bước sóng và tần số"),
                ConceptDTO(id="c2", title="Vận tốc truyền sóng"),
                ConceptDTO(id="c3", title="Sóng ngang và sóng dọc"),
                ConceptDTO(id="c4", title="Giao thoa sóng"),
            ],
            suggested_skills=["Biết công thức v = λ × f"],
        )

    def generate_learning_path(self, concepts, mastery_context, batch_size=3):
        batch = concepts[:batch_size]
        return LearningPathBatchResult(
            ordered_concept_ids=[c.id for c in batch],
            is_final_batch=len(concepts) <= batch_size,
        )

    def generate_lesson(self, concept, mastery_context, goal_context=None, material_context=None):
        concept_id = concept.id if hasattr(concept, "id") else concept.get("id", "c1")
        return LessonDTO(
            concept_id=concept_id,
            explanation="Giải thích mẫu (fake).",
            example="Ví dụ mẫu (fake).",
            key_points=["Điểm chính 1", "Điểm chính 2"],
            flashcards=[FlashcardDTO(front="Câu hỏi?", back="Trả lời")],
            cards=[
                LessonCardDTO(order_index=1, heading="Phần 1", body="Nội dung thẻ 1"),
                LessonCardDTO(order_index=2, heading="Phần 2", body="Nội dung thẻ 2"),
                LessonCardDTO(order_index=3, heading="Phần 3", body="Nội dung thẻ 3"),
            ],
        )

    def generate_check_question(
        self, concept, lesson, purpose, previous_misconceptions=None
    ):
        purpose_val = purpose.value if hasattr(purpose, "value") else str(purpose)
        if purpose_val == QuestionPurpose.CHECKPOINT.value:
            return CheckQuestionResult(
                questions=[
                    QuestionDTO(
                        text="Câu hỏi Checkpoint 1?",
                        options=[
                            QuestionOptionDTO(text="Đáp án A", is_correct=True),
                            QuestionOptionDTO(text="Đáp án B", is_correct=False),
                        ],
                        explanation="Giải thích checkpoint 1.",
                        purpose=purpose,
                        after_card_order=2,
                    )
                ]
            )
        else:
            return CheckQuestionResult(
                questions=[
                    QuestionDTO(
                        text="Câu hỏi Final Exam 1?",
                        options=[
                            QuestionOptionDTO(text="Đáp án A", is_correct=True),
                            QuestionOptionDTO(text="Đáp án B", is_correct=False),
                        ],
                        explanation="Giải thích final exam 1.",
                        purpose=purpose,
                        after_card_order=None,
                    ),
                    QuestionDTO(
                        text="Câu hỏi Final Exam 2?",
                        options=[
                            QuestionOptionDTO(text="Đáp án A", is_correct=True),
                            QuestionOptionDTO(text="Đáp án B", is_correct=False),
                        ],
                        explanation="Giải thích final exam 2.",
                        purpose=purpose,
                        after_card_order=None,
                    ),
                ]
            )

    def evaluate_answer(self, question, selected_option_index):
        is_correct = question.options[selected_option_index].is_correct
        return AnswerEvaluationResult(
            is_correct=is_correct,
            misconception=None if is_correct else "Nhầm lẫn công thức (fake)",
            confidence=0.9,
        )

    def decide_next_action(self, concept, evaluation_history):
        correct_count = sum(1 for e in evaluation_history if e.is_correct)
        total = len(evaluation_history)
        if total == 0:
            concept_id = concept.id if hasattr(concept, "id") else concept.get("id", "c1")
            return NextActionResult(action=NextAction.MOVE_NEXT, concept_id=concept_id)

        ratio = correct_count / total
        concept_id = concept.id if hasattr(concept, "id") else concept.get("id", "c1")
        if ratio >= 0.8:
            return NextActionResult(
                action=NextAction.MOVE_NEXT,
                concept_id=concept_id,
                needs_next_batch=True,
            )
        elif ratio >= 0.5:
            return NextActionResult(
                action=NextAction.PRACTICE_MORE, concept_id=concept_id
            )
        else:
            return NextActionResult(
                action=NextAction.EXPLAIN_AGAIN, concept_id=concept_id
            )

    def generate_hint(self, question, level, previous_hints):
        return HintResult(
            level=level, text=f"Gợi ý cấp {level} (fake) — không lộ đáp án."
        )

    def chat_reply(self, history, new_message, scope, learning_context=None):
        return ChatReplyResult(reply=f"(fake reply, scope={scope.value})")

    @staticmethod
    def _fake_question(purpose):
        return QuestionDTO(
            text="Câu hỏi mẫu?",
            options=[
                QuestionOptionDTO(text="Đáp án A", is_correct=True),
                QuestionOptionDTO(text="Đáp án B", is_correct=False),
            ],
            explanation="Giải thích mẫu.",
            purpose=purpose,
            after_card_order=1 if purpose == QuestionPurpose.CHECKPOINT else None,
        )
