from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


# ---- Data Transfer Objects ----

@dataclass
class LearningGoalDTO:
    title: str
    description: str

@dataclass
class AnalyzeMaterialResult:
    goals: List[LearningGoalDTO]
    suggested_skills: List[str]          # usefor Self-Check checkbox

@dataclass
class PathStepDTO:
    order: int
    title: str
    goal_refs: List[str]

@dataclass
class GeneratePathResult:
    steps: List[PathStepDTO]

@dataclass
class LessonCardDTO:
    order: int
    heading: str
    body: str

@dataclass
class GenerateLessonCardsResult:
    cards: List[LessonCardDTO]

@dataclass
class QuestionOptionDTO:
    text: str
    is_correct: bool

@dataclass
class QuestionDTO:
    text: str
    options: List[QuestionOptionDTO]
    explanation: str

@dataclass
class GenerateCheckpointResult:
    question: QuestionDTO

@dataclass
class GenerateFinalTestResult:
    questions: List[QuestionDTO]

@dataclass
class HintResult:
    level: int
    text: str

@dataclass
class ChatMessageDTO:
    role: str          # "student" | "ai"
    content: str

@dataclass
class ChatReplyResult:
    reply: str


class LLMServiceError(Exception):
    """Raised when the AI provider fails or returns malformed data."""
    pass


class LLMService(ABC):
    """
    Interface duy nhất mà toàn bộ app được phép gọi để tương tác AI.
    Không import adapter cụ thể (OpenRouter/Gemini) ở bất kỳ đâu ngoài
    factory/DI setup.
    Interface that can only can use to call all app that need to use AI.
    Don't import exactly adapter like (OpenRouter/Gemini) in anywhere that is not factory/ID setup.
    """

    @abstractmethod
    def analyze_material(self, material_content: str) -> AnalyzeMaterialResult: ...

    @abstractmethod
    def generate_path(self, goals: List[LearningGoalDTO]) -> GeneratePathResult: ...

    @abstractmethod
    def generate_lesson_cards(
        self, step: PathStepDTO, material_content: str
    ) -> GenerateLessonCardsResult: ...

    @abstractmethod
    def generate_checkpoint_question(
        self, cards: List[LessonCardDTO]
    ) -> GenerateCheckpointResult: ...

    @abstractmethod
    def generate_final_test(
        self, goals: List[LearningGoalDTO], all_cards: List[LessonCardDTO]
    ) -> GenerateFinalTestResult: ...

    @abstractmethod
    def generate_hint(
        self, question: QuestionDTO, level: int, previous_hints: List[str]
    ) -> HintResult:
        """
        level 1: gợi ý nhẹ, không hé lộ hướng giải (chotto)
        level 2: gợi ý rõ hơn, chỉ ra hướng tiếp cận (motto chotto)
        level 3: gần đáp án, học sinh vẫn phải tự hoàn thiện bước cuối (motto motto chotto)
        Không bao giờ trả đáp án trực tiếp ở bất kỳ cấp nào. (never giving the final answer for users)
        ---
        """
        ...

    @abstractmethod
    def chat_reply(
        self, history: List[ChatMessageDTO], new_message: str, scope: str
    ) -> ChatReplyResult:
        """scope: "material" (guardrail lỏng) | "quiz" (guardrail chặt)"""
        ...