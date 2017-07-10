import pytest

from swak.plugin import enumerate_plugins, BaseOutput
from swak.pipeline import build_pipeline_from_cmds, _parse_cmds


class DummyOutput(BaseOutput):
    pass


def test_pipeline(capsys):

    # Test parse run commands
    cmds = 'in.Counter --field 3 --max 2 | out.Stdout'
    pcmds = list(_parse_cmds(cmds))
    assert len(pcmds) == 2
    assert pcmds[0] == 'in.Counter --field 3 --max 2'
    assert pcmds[1] == 'out.Stdout'

    cmds = 'in.Counter --field=3 --max=2 |'
    pcmds = list(_parse_cmds(cmds))
    assert pcmds == ['in.Counter --field=3 --max=2']
    plugin_infos = list(enumerate_plugins())

    # Build pipeline from cmds
    cmds = 'in.Counter --field 3 --max 2 | out.Stdout'
    pipeline = build_pipeline_from_cmds(plugin_infos, cmds)

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

    #out, err = capsys.readouterr()
    #outs = out.split('\n')
    #assert '{"1": 1, "2": 1, "3": 1}' in out[0]
    #assert '{"1": 2, "2": 2, "3": 2}' in out[1]

    #cmds = 'in.Counter --field 3 --noparam 2 | out.Stdout'
    #with pytest.raises(SystemExit):
        #build_pipeline_from_cmds(plugin_infos, cmds)
