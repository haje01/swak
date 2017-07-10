import os
from subprocess import call

from swak.config import get_exe_dir
from swak.plugin import enumerate_plugins, get_plugins_dir
from swak.main import parse_test_commands


def test_plugin_cmd(capfd):
    cmd = ['swak', 'list']
    call(cmd)
    out, err = capfd.readouterr()
    assert 'Swak has {} plugin(s)'.format(1) in out

    cmd = ['swak', 'desc', 'in.Counter']
    import pdb; pdb.set_trace()  # XXX BREAKPOINT
    call(cmd)
    out, err = capfd.readouterr()
    assert "Emit incremental number" in out

    cmd = ['swak', 'desc', 'in.NotExist']
    call(cmd)
    out, err = capfd.readouterr()
    assert "Can not find" in err


def test_plugin_util():
    path = os.path.join(get_exe_dir(), 'plugins')
    assert path == get_plugins_dir()

    plugin_infos = list(enumerate_plugins())
    assert len(plugin_infos) > 0

    for pi in plugin_infos:
        print(pi)

    ret = list(parse_test_commands('in.Counter --fields 3 | out.Stdout'))
    assert len(ret) == 2
    assert ret[0][0] == 'in.Counter'
    assert ret[0][1] == '--fields'
    assert ret[0][2] == '3'
    assert ret[1][0] == 'out.Stdout'
