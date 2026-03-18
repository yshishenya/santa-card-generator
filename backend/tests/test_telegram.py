"""Unit tests for Telegram caption formatting."""

from src.integrations.telegram import TelegramClient


def test_format_caption_includes_only_escaped_name() -> None:
    """Telegram delivery should publish the image with the sender name only."""
    client = TelegramClient.__new__(TelegramClient)

    caption = client._format_caption("Катя <b>Гурова</b>")

    assert caption == "<b>Имя:</b> Катя &lt;b&gt;Гурова&lt;/b&gt;"
    assert "Альтер эго" not in caption
