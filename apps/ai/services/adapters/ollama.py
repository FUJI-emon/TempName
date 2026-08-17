"""
OllamaAdapter — implement LLMService bằng cách gọi Ollama local API (/api/generate).
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
    QuestionPurpose,
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


class OllamaAdapter(LLMService):
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen3:8b")
        self.timeout = int(os.getenv("OLLAMA_TIMEOUT", "180"))

    def _call(self, system_prompt: str, user_prompt: str) -> dict:
        """Gọi Ollama /api/generate, ép JSON output, parse và trả dict."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
            "format": "json",
            "think": False,
            "options": {
                "temperature": 0,
                "num_predict": 1500,
    },

        }
        try:
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise LLMServiceError(f"Gọi Ollama thất bại: {exc}") from exc

        try:
            resp_json = response.json()
            if "response" not in resp_json:
                raise LLMInvalidResponseError("Ollama response thiếu field 'response'")
            content = str(resp_json["response"]).strip()

            print("\n===== OLLAMA RAW RESPONSE =====")
            print(content)
            print("===== END RAW RESPONSE =====\n")
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            return json.loads(content)
        except (KeyError, json.JSONDecodeError, TypeError) as exc:
            raise LLMInvalidResponseError(f"Ollama trả response không hợp lệ: {exc}") from exc

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
                ConceptDTO(id=str(c["id"]), title=c["title"], description=c.get("description", ""))
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
                ordered_concept_ids=[str(cid) for cid in ordered_ids],
                is_final_batch=bool(data.get("is_final_batch", len(concepts) <= batch_size)),
            )
        except (KeyError, TypeError) as exc:
            raise LLMInvalidResponseError(f"Response thiếu/lỗi field trong generate_learning_path: {exc}") from exc

    def generate_lesson(self, concept, mastery_context, goal_context=None, material_context=None):
        system_prompt = generate_lesson_prompts.SYSTEM_PROMPT
        user_prompt = generate_lesson_prompts.build_user_prompt(
            concept, mastery_context, goal_context, material_context
        )
        data = self._call(system_prompt, user_prompt)

        try:
            flashcards = [
                FlashcardDTO(front=f["front"], back=f["back"])
                for f in data.get("flashcards", [])
            ]
            cards = [
                LessonCardDTO(
                    order_index=c.get("order_index", idx + 1),
                    heading=c["heading"],
                    body=c["body"],
                )
                for idx, c in enumerate(data.get("cards", []))
            ]
            concept_id = concept.id if hasattr(concept, "id") else concept.get("id", data.get("concept_id", ""))
            return LessonDTO(
                concept_id=str(concept_id),
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
            for q_data in data.get("questions", []):
                options = []
                raw_options = q_data.get("options", [])
                has_correct = False
                for idx, opt in enumerate(raw_options):
                    is_corr = bool(opt.get("is_correct", opt.get("correct", False)))
                    if is_corr:
                        has_correct = True
                    options.append(
                        QuestionOptionDTO(
                            text=opt.get("text", f"Lựa chọn {idx+1}"),
                            is_correct=is_corr
                        )
                    )
                if options and not has_correct:
                    options[0].is_correct = True

                after_card_order = None
                purpose_val = purpose.value if hasattr(purpose, "value") else str(purpose)
                if purpose_val == QuestionPurpose.CHECKPOINT.value:
                    after_card_order = q_data.get("after_card_order")
                    if after_card_order is None:
                        total_cards = len(getattr(lesson, "cards", [])) if hasattr(lesson, "cards") else (len(lesson.get("cards", [])) if isinstance(lesson, dict) else 1)
                        after_card_order = max(1, total_cards // 2)

                if options:
                    questions.append(
                        QuestionDTO(
                            text=q_data.get("text", "Câu hỏi kiểm tra kiến thức"),
                            options=options,
                            explanation=q_data.get("explanation", "Lời giải thích đáp án."),
                            purpose=purpose,
                            after_card_order=after_card_order,
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
            return NextActionResult(action=NextAction.MOVE_NEXT, concept_id=str(concept_id))

        system_prompt = decide_next_action_prompts.SYSTEM_PROMPT
        user_prompt = decide_next_action_prompts.build_user_prompt(concept, evaluation_history)
        data = self._call(system_prompt, user_prompt)

        try:
            action_enum = NextAction(data["action"])
            return NextActionResult(
                action=action_enum,
                concept_id=str(data.get("concept_id", concept_id)),
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
        assert_no_leak(result.text, question)
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
