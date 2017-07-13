import pytest

from swak.plugin import BaseOutput
from swak.pipeline import build_pipeline_from_cmds, _parse_cmds


class DummyOutput(BaseOutput):
    pass


def test_pipeline(capsys):

    # Test parse run commands
    cmds = 'in.counter --field 3 --max 2 | out.stdout'
    pcmds = list(_parse_cmds(cmds))
    assert len(pcmds) == 2
    assert pcmds[0] == 'in.counter --field 3 --max 2'
    assert pcmds[1] == 'out.stdout'

    cmds = 'in.counter --field=3 --max=2 |'
    pcmds = list(_parse_cmds(cmds))
    assert pcmds == ['in.counter --field=3 --max=2']

    # Build pipeline from cmds
    cmds = 'in.counter --field 3 --max 2 | out.stdout'
    pipeline = build_pipeline_from_cmds(cmds)

    with pytest.raises(RuntimeError):
        pipeline.step()
    with pytest.raises(RuntimeError):
        pipeline.stop()

    # Validate plugins
    pipeline.validate()

    opl = pipeline.plugins
    plugins = pipeline.plugins[:]
    plugins.insert(0, DummyOutput())
    pipeline.plugins = plugins
    with pytest.raises(ValueError):
        pipeline.validate()
    pipeline.plugins = opl

    # Start pipeline
    pipeline.start()
    for plugin in pipeline.plugins:
        assert plugin.started == True

    # Step pipeline
    pipeline.step()

    # Stop pipeline
    pipeline.stop()
    for plugin in pipeline.plugins:
        assert plugin.started == False

    # Terminiate pipeline
    pipeline.terminate()
    for plugin in pipeline.plugins:
        assert plugin.terminated == True
