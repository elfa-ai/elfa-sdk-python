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


async def test_aiter_sse():
    async def lines():
        for line in ["event: update", 'data: {"n":2}', ""]:
            yield line

    messages = [m async for m in aiter_sse(lines())]
    assert messages[0].event == "update"
    assert messages[0].data == '{"n":2}'
