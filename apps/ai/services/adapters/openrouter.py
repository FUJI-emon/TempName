"""
OpenRouterAdapter — implement LLMService bằng cách gọi OpenRouter API.
Pattern chung cho mọi method:
  1. Validate input (nếu cần) -> raise LLMEmptyInputError
  2. Build prompt từ apps/ai/services/prompts/<method>.py
  3. self._call(system_prompt, user_prompt) -> dict (đã parse JSON)
  4. Map dict -> đúng DTO, bọc try/except -> raise LLMInvalidResponseError nếu sai format
  5. Riêng generate_hint và chat_reply(scope=QUIZ): LUÔN chạy assert_no_leak trước khi return
     (guardrail chặn ngay tại nguồn, không chờ orchestrator phát hiện).
"""
import json
import os

import requests

from ..dto import (
    AnalyzeMaterialResult,
    AnswerEvaluationResult,
    ChatReplyResult,
    ChatScope,
    CheckQuestionResult,
    ConceptDTO,
    ConversationResult,
    FlashcardDTO,
    HintResult,
    LearningPathBatchResult,
    LessonCardDTO,
    LessonDTO,
    NextAction,
    NextActionResult,
    QuestionDTO,
    QuestionOptionDTO,
)
from ..exceptions import LLMEmptyInputError, LLMInvalidResponseError, LLMServiceError
from ..guardrail import assert_no_leak, assert_no_leak_chat
from ..interface import LLMService
from ..prompts import analyze_material as analyze_prompts
from ..prompts import chat_reply as chat_reply_prompts
from ..prompts import decide_next_action as decide_next_action_prompts
from ..prompts import evaluate_answer as evaluate_answer_prompts
from ..prompts import generate_check_question as generate_check_question_prompts
from ..prompts import generate_learning_path as generate_learning_path_prompts
from ..prompts import generate_lesson as generate_lesson_prompts
from ..prompts import hint as hint_prompts
from ..prompts import start_conversation as start_conversation_prompts


class OpenRouterAdapter(LLMService):
    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, model: str = None, api_key: str = None):
        self.model = model or os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise LLMServiceError("Thiếu OPENROUTER_API_KEY trong environment")

    def _call(self, system_prompt: str, user_prompt: str) -> dict:
        """Gọi OpenRouter, ép JSON output, parse và trả dict."""
        try:
            response = requests.post(
                self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.4,
                },
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise LLMServiceError(f"Gọi OpenRouter thất bại: {exc}") from exc

        try:
            content = response.json()["choices"][0]["message"]["content"]
            return json.loads(content)
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise LLMInvalidResponseError(f"OpenRouter trả response không hợp lệ: {exc}") from exc

    def start_conversation(self, user_message, uploaded_material=None):
        if not user_message or not user_message.strip():
            raise LLMEmptyInputError("user_message không được để trống")

        system_prompt = start_conversation_prompts.SYSTEM_PROMPT
        user_prompt = start_conversation_prompts.build_user_prompt(user_message, uploaded_material)
        data = self._call(system_prompt, user_prompt)

        try:
            return ConversationResult(
                reply=data["reply"],
                ready_to_analyze=bool(data.get("ready_to_analyze", False)),
                detected_goal=data.get("detected_goal"),
            )
        except (KeyError, TypeError) as exc:
            raise LLMInvalidResponseError(f"Response thiếu/lỗi field trong start_conversation: {exc}") from exc

    def analyze_material(self, material_content, goal):
        if not material_content or not material_content.strip():
            raise LLMEmptyInputError("material_content không được để trống")

        system_prompt = analyze_prompts.SYSTEM_PROMPT
        user_prompt = analyze_prompts.build_user_prompt(material_content, goal)
        data = self._call(system_prompt, user_prompt)

        try:
            concepts = [
                ConceptDTO(id=c["id"], title=c["title"], description=c.get("description", ""))
                for c in data["concepts"]
            ]
        except (KeyError, TypeError) as exc:
            raise LLMInvalidResponseError(f"Response thiếu/lỗi field concepts: {exc}") from exc

        return AnalyzeMaterialResult(
            concepts=concepts,
            suggested_skills=data.get("suggested_skills", []),
        )

    def generate_learning_path(self, concepts, mastery_context, batch_size=3):
        if not concepts:
            return LearningPathBatchResult(ordered_concept_ids=[], is_final_batch=True)

        system_prompt = generate_learning_path_prompts.SYSTEM_PROMPT
        user_prompt = generate_learning_path_prompts.build_user_prompt(concepts, mastery_context, batch_size)
        data = self._call(system_prompt, user_prompt)

        try:
            ordered_ids = data.get("ordered_concept_ids") or data.get("concept_ids") or data.get("ordered_concepts")
            if not ordered_ids or not isinstance(ordered_ids, list):
                ordered_ids = [c.id if hasattr(c, "id") else c["id"] for c in concepts[:batch_size]]

            return LearningPathBatchResult(
                ordered_concept_ids=ordered_ids,
                is_final_batch=bool(data.get("is_final_batch", len(concepts) <= batch_size)),
            )
        except (KeyError, TypeError) as exc:
            raise LLMInvalidResponseError(f"Response thiếu/lỗi field trong generate_learning_path: {exc}") from exc


    def generate_lesson(self, concept, mastery_context):
        system_prompt = generate_lesson_prompts.SYSTEM_PROMPT
        user_prompt = generate_lesson_prompts.build_user_prompt(concept, mastery_context)
        data = self._call(system_prompt, user_prompt)

        try:
            flashcards = [
                FlashcardDTO(front=f["front"], back=f["back"])
                for f in data.get("flashcards", [])
            ]
            cards = [
                LessonCardDTO(
                    order_index=c.get("order_index", idx),
                    heading=c["heading"],
                    body=c["body"],
                )
                for idx, c in enumerate(data.get("cards", []))
            ]
            concept_id = concept.id if hasattr(concept, "id") else concept.get("id", data.get("concept_id", ""))
            return LessonDTO(
                concept_id=concept_id,
                explanation=data["explanation"],
                example=data.get("example", ""),
                key_points=data.get("key_points", []),
                flashcards=flashcards,
                cards=cards,
            )
        except (KeyError, TypeError) as exc:
            raise LLMInvalidResponseError(f"Response thiếu/lỗi field trong generate_lesson: {exc}") from exc

    def generate_check_question(self, concept, lesson, purpose, previous_misconceptions=None):
        system_prompt = generate_check_question_prompts.SYSTEM_PROMPT
        user_prompt = generate_check_question_prompts.build_user_prompt(
            concept, lesson, purpose, previous_misconceptions
        )
        data = self._call(system_prompt, user_prompt)

        try:
            questions = []
            for q_data in data["questions"]:
                options = [
                    QuestionOptionDTO(text=opt["text"], is_correct=bool(opt["is_correct"]))
                    for opt in q_data["options"]
                ]
                questions.append(
                    QuestionDTO(
                        text=q_data["text"],
                        options=options,
                        explanation=q_data.get("explanation", ""),
                        purpose=purpose,
                    )
                )
            return CheckQuestionResult(questions=questions)
        except (KeyError, TypeError) as exc:
            raise LLMInvalidResponseError(f"Response thiếu/lỗi field trong generate_check_question: {exc}") from exc

    def evaluate_answer(self, question, selected_option_index):
        if selected_option_index < 0 or selected_option_index >= len(question.options):
            raise IndexError("selected_option_index ngoài phạm vi danh sách phương án")

        system_prompt = evaluate_answer_prompts.SYSTEM_PROMPT
        user_prompt = evaluate_answer_prompts.build_user_prompt(question, selected_option_index)
        data = self._call(system_prompt, user_prompt)

        try:
            return AnswerEvaluationResult(
                is_correct=bool(data["is_correct"]),
                misconception=data.get("misconception"),
                confidence=float(data.get("confidence", 1.0)),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise LLMInvalidResponseError(f"Response thiếu/lỗi field trong evaluate_answer: {exc}") from exc

    def decide_next_action(self, concept, evaluation_history):
        concept_id = concept.id if hasattr(concept, "id") else concept.get("id", "")
        if not evaluation_history:
            return NextActionResult(action=NextAction.MOVE_NEXT, concept_id=concept_id)

        system_prompt = decide_next_action_prompts.SYSTEM_PROMPT
        user_prompt = decide_next_action_prompts.build_user_prompt(concept, evaluation_history)
        data = self._call(system_prompt, user_prompt)

        try:
            action_enum = NextAction(data["action"])
            return NextActionResult(
                action=action_enum,
                concept_id=data.get("concept_id", concept_id),
                reasoning=data.get("reasoning", ""),
                needs_next_batch=bool(data.get("needs_next_batch", False)),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise LLMInvalidResponseError(f"Response thiếu/lỗi field trong decide_next_action: {exc}") from exc

    def generate_hint(self, question, level, previous_hints):
        system_prompt = hint_prompts.SYSTEM_PROMPT
        user_prompt = hint_prompts.build_user_prompt(question, level, previous_hints)
        data = self._call(system_prompt, user_prompt)

        try:
            hint_text = data["hint"]
        except KeyError as exc:
            raise LLMInvalidResponseError("Response thiếu field 'hint'") from exc

        result = HintResult(level=level, text=hint_text)
        assert_no_leak(result.text, question)  # chặn ngay tại nguồn
        return result

    def chat_reply(self, history, new_message, scope, learning_context=None):
        if not new_message or not new_message.strip():
            raise LLMEmptyInputError("new_message không được để trống")

        system_prompt = chat_reply_prompts.SYSTEM_PROMPT
        user_prompt = chat_reply_prompts.build_user_prompt(history, new_message, scope, learning_context)
        data = self._call(system_prompt, user_prompt)

        try:
            reply_text = data["reply"]
        except (KeyError, TypeError) as exc:
            raise LLMInvalidResponseError(f"Response thiếu field 'reply': {exc}") from exc

        scope_val = scope.value if hasattr(scope, "value") else str(scope)
        if scope_val == ChatScope.QUIZ.value:
            current_q = getattr(learning_context, "current_question", None) if learning_context else None
            assert_no_leak_chat(reply_text, current_q)

        return ChatReplyResult(reply=reply_text)