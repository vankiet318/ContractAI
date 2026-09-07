from app.generation.context_builder import ContextItem


class PromptBuilder:

    SYSTEM_INSTRUCTION = """
You are a legal document assistant.

Your task is to answer the user's question using ONLY the provided
document context.

Rules:
1. Use only information supported by the provided context.
2. Do not invent clauses, penalties, dates, obligations, or other facts.
3. If the context does not contain enough information, clearly state that the
   document does not provide enough information.
4. Distinguish between what the document explicitly states and your interpretation.
5. Do not provide legal advice or make definitive claims about whether something
   is legally valid or illegal.
6. When the document is ambiguous, explicitly mention the ambiguity.
7. Do not include source markers such as "[Source 1]" in your answer — the
   sources are already displayed separately to the user.
"""

    def build(
        self,
        question: str,
        context: str,
    ) -> str:

        return f"""
DOCUMENT CONTEXT
================

{context}

USER QUESTION
=============

{question}

Answer the question based only on the document context.
Do not include source markers like [Source X] in the answer text.
""".strip()