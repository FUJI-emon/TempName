SYSTEM_PROMPT = """Bạn phân tích tài liệu học tập và mục tiêu học (goal) do giáo viên/học
sinh cung cấp, trả về danh sách concept (khái niệm) cần học để đạt mục tiêu đó.
Trả JSON đúng format:
{"concepts": [{"id": "c1", "title": "...", "description": "..."}], "suggested_skills": ["..."]}
Không thêm text ngoài JSON. id dùng format c1, c2, c3..."""


def build_user_prompt(material_content: str, goal: str) -> str:
    return f"""Tài liệu học tập:
{material_content}

Mục tiêu học (giáo viên mong muốn học sinh đạt được):
{goal}

Phân tích và trả về danh sách concept theo đúng JSON format."""