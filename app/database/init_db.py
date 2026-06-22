import logging
import time

from sqlalchemy.exc import OperationalError

from app.database.base import Base
from app.database.session import engine
from app.models.document import Document  # noqa: F401

logger = logging.getLogger(__name__)


def init_db(retries: int = 30, delay_seconds: int = 2) -> None:
    for attempt in range(1, retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database schema is ready")
            return
        except OperationalError as exc:
            if attempt == retries:
                raise
            logger.warning("Database unavailable, retrying %s/%s: %s", attempt, retries, exc)
            time.sleep(delay_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
