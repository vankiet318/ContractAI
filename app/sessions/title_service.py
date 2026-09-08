from app.sessions.models import ChatSession
from app.sessions.service import SessionService
from app.sessions.title_generator import SessionTitleGenerator


class SessionTitleService:

    def __init__(
        self,
        session_service: SessionService,
        title_generator: SessionTitleGenerator,
    ):
        self.session_service = session_service
        self.title_generator = title_generator

    def maybe_generate_title(
        self,
        session: ChatSession,
        question: str,
    ) -> str | None:

        if not session.title_is_default:
            return None

        try:
            title = self.title_generator.generate(question)
        except Exception:
            # Best-effort: keep the placeholder title, retry on the
            # session's next query rather than failing the request.
            return None

        if not title:
            return None

        self.session_service.update_title(
            session_id=session.session_id,
            title=title,
        )

        return title
