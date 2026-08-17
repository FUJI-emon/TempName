import json
from unittest.mock import MagicMock, patch

from django.test import TestCase
import requests

from apps.ai.services.adapters.ollama import OllamaAdapter
from apps.ai.services.dto import (
    ChatScope,
    ConceptDTO,
    LessonDTO,
    QuestionDTO,
    QuestionOptionDTO,
    QuestionPurpose,
)
from apps.ai.services.exceptions import (
    LLMEmptyInputError,
    LLMInvalidResponseError,
    LLMServiceError,
)
from apps.ai.services.factory import get_llm_service


class OllamaAdapterTest(TestCase):
    def setUp(self):
        self.adapter = OllamaAdapter(base_url="http://localhost:11434", model="qwen3:8b")

    @patch("requests.post")
    def test_start_conversation_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "response": json.dumps({
                "reply": "Chào bạn! Mình có thể giúp gì?",
                "ready_to_analyze": True,
                "detected_goal": "Đạo hàm lớp 12"
            })
        }
        mock_post.return_value = mock_resp

        result = self.adapter.start_conversation("Tôi muốn học đạo hàm")
        self.assertEqual(result.reply, "Chào bạn! Mình có thể giúp gì?")
        self.assertTrue(result.ready_to_analyze)
        self.assertEqual(result.detected_goal, "Đạo hàm lớp 12")

        # Verify endpoint and request payload format
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "http://localhost:11434/api/generate")
        self.assertEqual(kwargs["json"]["model"], "qwen3:8b")
        self.assertEqual(kwargs["json"]["format"], "json")
        self.assertFalse(kwargs["json"]["stream"])

    @patch("requests.post")
    def test_analyze_material_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "response": json.dumps({
                "concepts": [
                    {"id": "c1", "title": "Khái niệm Đạo hàm", "description": "Định nghĩa và ý nghĩa"},
                    {"id": "c2", "title": "Quy tắc tính đạo hàm", "description": "Các công thức cơ bản"}
                ],
                "suggested_skills": ["Tính đạo hàm"]
            })
        }
        mock_post.return_value = mock_resp

        result = self.adapter.analyze_material("Nội dung tài liệu...", "Mục tiêu")
        self.assertEqual(len(result.concepts), 2)
        self.assertEqual(result.concepts[0].id, "c1")
        self.assertEqual(result.concepts[0].title, "Khái niệm Đạo hàm")

    @patch("requests.post")
    def test_generate_learning_path_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "response": json.dumps({
                "ordered_concept_ids": ["c1", "c2"],
                "is_final_batch": True
            })
        }
        mock_post.return_value = mock_resp

        concepts = [ConceptDTO(id="c1", title="C1"), ConceptDTO(id="c2", title="C2")]
        result = self.adapter.generate_learning_path(concepts, mastery_context={})
        self.assertEqual(result.ordered_concept_ids, ["c1", "c2"])
        self.assertTrue(result.is_final_batch)

    @patch("requests.post")
    def test_generate_lesson_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "response": json.dumps({
                "explanation": "Giải thích đạo hàm",
                "example": "y = x^2 => y' = 2x",
                "key_points": ["Điểm 1"],
                "flashcards": [{"front": "Q1", "back": "A1"}],
                "cards": [{"order_index": 1, "heading": "Card 1", "body": "Body 1"}]
            })
        }
        mock_post.return_value = mock_resp

        concept = ConceptDTO(id="c1", title="Đạo hàm")
        result = self.adapter.generate_lesson(concept, mastery_context={})
        self.assertEqual(result.explanation, "Giải thích đạo hàm")
        self.assertEqual(len(result.cards), 1)

    @patch("requests.post")
    def test_generate_check_question_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "response": json.dumps({
                "questions": [
                    {
                        "text": "Đạo hàm của x^2 là gì?",
                        "options": [
                            {"text": "2x", "is_correct": True},
                            {"text": "x", "is_correct": False}
                        ],
                        "explanation": "(x^2)' = 2x",
                        "after_card_order": 1
                    }
                ]
            })
        }
        mock_post.return_value = mock_resp

        concept = ConceptDTO(id="c1", title="C1")
        lesson = LessonDTO(concept_id="c1", explanation="E", example="X", key_points=[], flashcards=[], cards=[])
        result = self.adapter.generate_check_question(concept, lesson, QuestionPurpose.CHECKPOINT)
        self.assertEqual(len(result.questions), 1)
        self.assertTrue(result.questions[0].options[0].is_correct)

    @patch("requests.post")
    def test_evaluate_answer_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "response": json.dumps({
                "is_correct": True,
                "confidence": 0.95
            })
        }
        mock_post.return_value = mock_resp

        q = QuestionDTO(
            text="Q?",
            options=[QuestionOptionDTO(text="O1", is_correct=True)],
            explanation="Exp",
            purpose=QuestionPurpose.CHECKPOINT
        )
        result = self.adapter.evaluate_answer(q, selected_option_index=0)
        self.assertTrue(result.is_correct)

    @patch("requests.post")
    def test_decide_next_action_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "response": json.dumps({
                "action": "move_next",
                "reasoning": "Học sinh trả lời đúng",
                "needs_next_batch": False
            })
        }
        mock_post.return_value = mock_resp

        concept = ConceptDTO(id="c1", title="C1")
        result = self.adapter.decide_next_action(concept, evaluation_history=[MagicMock(is_correct=True)])
        self.assertEqual(result.action.value, "move_next")

    @patch("requests.post")
    def test_generate_hint_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "response": json.dumps({
                "hint": "Hãy sử dụng công thức tính đạo hàm bậc nhất"
            })
        }
        mock_post.return_value = mock_resp

        q = QuestionDTO(
            text="Tính đạo hàm của x^2",
            options=[QuestionOptionDTO(text="Phương án hai x", is_correct=True)],
            explanation="Exp",
            purpose=QuestionPurpose.CHECKPOINT
        )
        result = self.adapter.generate_hint(q, level=1, previous_hints=[])
        self.assertEqual(result.text, "Hãy sử dụng công thức tính đạo hàm bậc nhất")

    @patch("requests.post")
    def test_chat_reply_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "response": json.dumps({
                "reply": "Đây là giải thích thêm cho câu hỏi."
            })
        }
        mock_post.return_value = mock_resp

        result = self.adapter.chat_reply(history=[], new_message="Giải thích giúp tôi", scope=ChatScope.GOAL)
        self.assertEqual(result.reply, "Đây là giải thích thêm cho câu hỏi.")

    def test_empty_input_validation(self):
        with self.assertRaises(LLMEmptyInputError):
            self.adapter.start_conversation("")

        with self.assertRaises(LLMEmptyInputError):
            self.adapter.analyze_material(" ", "Goal")

        with self.assertRaises(LLMEmptyInputError):
            self.adapter.chat_reply([], "   ", ChatScope.GOAL)

    @patch("requests.post")
    def test_http_network_failure_raises_llm_service_error(self, mock_post):
        mock_post.side_effect = requests.RequestException("Connection refused")

        with self.assertRaises(LLMServiceError) as cm:
            self.adapter.start_conversation("Xin chào")
        self.assertIn("Gọi Ollama thất bại", str(cm.exception))

    @patch("requests.post")
    def test_invalid_json_response_raises_llm_invalid_response_error(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"response": "This is not json"}
        mock_post.return_value = mock_resp

        with self.assertRaises(LLMInvalidResponseError):
            self.adapter.start_conversation("Xin chào")

    @patch.dict("os.environ", {"LLM_PROVIDER": "ollama"})
    def test_factory_returns_ollama_adapter(self):
        service = get_llm_service()
        self.assertIsInstance(service, OllamaAdapter)
