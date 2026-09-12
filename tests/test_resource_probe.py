"""resource_probe must never raise, and must return None (not a guessed
number) when a value genuinely can't be measured."""
from research_os.core.resource_probe import gpu_vram_usage_mb, process_ram_mb


def test_process_ram_mb_returns_none_for_nonexistent_process():
    assert process_ram_mb("definitely-not-a-real-process-xyz") is None


def test_process_ram_mb_never_raises():
    # Should not raise even with a weird process name.
    result = process_ram_mb("")
    assert result is None or isinstance(result, float)


def test_gpu_vram_usage_mb_never_raises():
    result = gpu_vram_usage_mb()
    assert result is None or isinstance(result, float)
