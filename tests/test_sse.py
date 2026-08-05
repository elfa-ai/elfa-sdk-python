"""SSE frame parsing (sync + async)."""

from elfa.utils.sse import SSEMessage, aiter_sse, iter_sse


def test_iter_sse_parses_frames():
    lines = [
        "event: triggered",
        'data: {"x":1}',
        "id: 5",
        "",
        "event: end",
        "data: {}",
        "",
    ]
    messages = list(iter_sse(iter(lines)))
    assert messages[0] == SSEMessage(event="triggered", data='{"x":1}', id="5")
    assert messages[1].event == "end"


def test_iter_sse_multiline_data_and_comments():
    lines = [": keep-alive", "data: a", "data: b", ""]
    (message,) = list(iter_sse(iter(lines)))
    assert message.event == "message"
    assert message.data == "a\nb"


def test_iter_sse_flushes_trailing_frame():
    (message,) = list(iter_sse(iter(["data: last"])))
    assert message.data == "last"


def test_iter_sse_crlf_line_endings():
    lines = ["event: x\r", "data: y\r", ""]
    (message,) = list(iter_sse(iter(lines)))
    assert message == SSEMessage(event="x", data="y", id=None)


def test_iter_sse_comment_only_frame_dropped():
    messages = list(iter_sse(iter([": ping", "", "event: x", "data: y", ""])))
    assert len(messages) == 1
    assert messages[0].event == "x"


def test_iter_sse_event_with_no_data():
    (message,) = list(iter_sse(iter(["event: end", ""])))
    assert message == SSEMessage(event="end", data="", id=None)


def test_iter_sse_done_literal_passthrough():
    (message,) = list(iter_sse(iter(["data: [DONE]", ""])))
    assert message.data == "[DONE]"
    assert message.event == "message"


async def test_aiter_sse():
    async def lines():
        for line in ["event: update", 'data: {"n":2}', ""]:
            yield line

    messages = [m async for m in aiter_sse(lines())]
    assert messages[0].event == "update"
    assert messages[0].data == '{"n":2}'


async def test_aiter_sse_crlf_and_comment():
    async def lines():
        for line in [": ping\r", "", "event: end\r", "data: {}\r", ""]:
            yield line

    messages = [m async for m in aiter_sse(lines())]
    assert len(messages) == 1
    assert messages[0] == SSEMessage(event="end", data="{}", id=None)
