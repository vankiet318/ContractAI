import logging

from app.logs.buffer import LogBuffer


def make_logger(buffer, name="app.test"):
    logger = logging.getLogger(name)
    logger.handlers = [buffer]
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    return logger


def test_newest_entries_come_first():
    buffer = LogBuffer(capacity=10)
    logger = make_logger(buffer)

    logger.info("first %s", 1)
    logger.warning("second")

    entries = buffer.newest(limit=10)

    assert [entry.message for entry in entries] == ["second", "first 1"]
    assert [entry.level for entry in entries] == ["WARNING", "INFO"]
    assert entries[0].logger == "app.test"
    assert entries[0].created_at.tzinfo is not None


def test_oldest_entries_are_dropped_beyond_capacity():
    buffer = LogBuffer(capacity=2)
    logger = make_logger(buffer)

    for index in range(3):
        logger.info("line %d", index)

    assert [entry.message for entry in buffer.newest(limit=10)] == [
        "line 2",
        "line 1",
    ]


def test_limit_keeps_the_newest():
    buffer = LogBuffer(capacity=10)
    logger = make_logger(buffer)

    for index in range(3):
        logger.info("line %d", index)

    assert [entry.message for entry in buffer.newest(limit=1)] == ["line 2"]


def test_below_handler_level_is_not_kept():
    buffer = LogBuffer(capacity=10)
    logger = make_logger(buffer)

    logger.debug("noise")

    assert buffer.newest(limit=10) == []


def test_exception_traceback_is_kept():
    buffer = LogBuffer(capacity=10)
    logger = make_logger(buffer)

    try:
        raise ValueError("broken pdf")
    except ValueError:
        logger.exception("Indexing failed")

    entry = buffer.newest(limit=1)[0]

    assert entry.message == "Indexing failed"
    assert "ValueError: broken pdf" in entry.exception


def test_requests_of_the_log_page_itself_are_not_kept():
    buffer = LogBuffer(capacity=10)
    access = make_logger(buffer, name="uvicorn.access")

    access.info('%s - "%s %s HTTP/%s" %d', "1.2.3.4", "GET", "/admin/logs?limit=1000", "1.1", 200)
    access.info('%s - "%s %s HTTP/%s" %d', "1.2.3.4", "GET", "/sessions", "1.1", 200)

    assert [entry.message for entry in buffer.newest(limit=10)] == [
        '1.2.3.4 - "GET /sessions HTTP/1.1" 200',
    ]
