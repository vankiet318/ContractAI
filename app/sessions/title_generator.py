from app.generation.base import LLM

MAX_TITLE_LENGTH = 60

_PROMPT_TEMPLATE = (
    "Tóm tắt câu hỏi sau thành một tiêu đề ngắn gọn cho đoạn chat, "
    "tối đa 6 từ, không dùng dấu ngoặc kép, không giải thích thêm, "
    "chỉ trả về đúng tiêu đề:\n\n{question}"
)


class SessionTitleGenerator:

    def __init__(self, llm: LLM):
        self.llm = llm

    def generate(self, question: str) -> str:
        prompt = _PROMPT_TEMPLATE.format(question=question)

        raw_title = self.llm.generate(prompt).strip()

        if not raw_title:
            return ""

        title = raw_title.splitlines()[0].strip('"\' ')

        return title[:MAX_TITLE_LENGTH]
