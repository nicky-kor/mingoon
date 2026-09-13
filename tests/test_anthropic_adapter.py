"""AnthropicAdapter.generate() against a mocked anthropic.Anthropic client.

No other test exercised this path (everything else mocks ProviderAdapter
itself), which is exactly how a real SDK signature mismatch
(messages.create() no longer accepting `temperature` directly in newer
anthropic releases) slipped through until it was hit for real — see
docs/autonomous-session-report.md.
"""
import sys
import types

import pytest

from research_os.models.base import GenerationRequest, ModelUnavailableError


class _FakeTextBlock:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class _FakeUsage:
    def __init__(self, input_tokens, output_tokens):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class _FakeMessage:
    def __init__(self, text, input_tokens=10, output_tokens=5):
        self.content = [_FakeTextBlock(text)]
        self.usage = _FakeUsage(input_tokens, output_tokens)


@pytest.fixture()
def fake_anthropic_module(monkeypatch):
    """Installs a minimal fake `anthropic` module so AnthropicAdapter's
    lazy `import anthropic` picks it up, without needing the real package
    or a real API key."""
    captured = {}

    class FakeMessages:
        def create(self, **kwargs):
            captured["kwargs"] = kwargs
            return _FakeMessage("hello from claude")

    class FakeAnthropic:
        def __init__(self, api_key):
            captured["api_key"] = api_key
            self.messages = FakeMessages()

    fake_module = types.SimpleNamespace(Anthropic=FakeAnthropic)
    monkeypatch.setitem(sys.modules, "anthropic", fake_module)
    return captured


def test_generate_passes_temperature_via_extra_body_not_as_a_direct_kwarg(fake_anthropic_module):
    from research_os.models.anthropic import AnthropicAdapter

    adapter = AnthropicAdapter(api_key="sk-ant-test-not-real")
    result = adapter.generate(GenerationRequest(prompt="hi", temperature=0.3), "claude-haiku-4-5-20251001")

    assert result.text == "hello from claude"
    assert result.provider == "anthropic"
    assert result.input_tokens == 10
    assert result.output_tokens == 5

    kwargs = fake_anthropic_module["kwargs"]
    # Regression guard: newer anthropic SDK releases dropped `temperature`
    # from messages.create()'s typed signature — passing it as a direct
    # kwarg raises "unexpected keyword argument 'temperature'". It must go
    # through extra_body instead, and never as a top-level kwarg.
    assert "temperature" not in kwargs
    assert kwargs["extra_body"] == {"temperature": 0.3}
    assert kwargs["model"] == "claude-haiku-4-5-20251001"
    assert kwargs["messages"] == [{"role": "user", "content": "hi"}]


def test_generate_wraps_sdk_errors_as_model_unavailable(monkeypatch):
    from research_os.models.anthropic import AnthropicAdapter

    class RaisingMessages:
        def create(self, **kwargs):
            raise TypeError("Messages.create() got an unexpected keyword argument 'temperature'")

    class RaisingAnthropic:
        def __init__(self, api_key):
            self.messages = RaisingMessages()

    monkeypatch.setitem(sys.modules, "anthropic", types.SimpleNamespace(Anthropic=RaisingAnthropic))

    adapter = AnthropicAdapter(api_key="sk-ant-test-not-real")
    with pytest.raises(ModelUnavailableError):
        adapter.generate(GenerationRequest(prompt="hi"), "claude-haiku-4-5-20251001")


def test_is_available_false_without_api_key(monkeypatch):
    from research_os.models.anthropic import AnthropicAdapter

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert AnthropicAdapter(api_key=None).is_available() is False


def test_generate_raises_without_api_key():
    from research_os.models.anthropic import AnthropicAdapter

    adapter = AnthropicAdapter(api_key=None)
    with pytest.raises(ModelUnavailableError):
        adapter.generate(GenerationRequest(prompt="hi"), "claude-haiku-4-5-20251001")
