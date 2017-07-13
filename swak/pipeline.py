import re
import sys
import logging


from swak.plugin import BaseInput
import swak.plugins


cmd_ptrn = re.compile(r'\S*(?P<cmd>((in\.|par\.|tr\.|buf\.|out\.|cmd\.)\S+)'
                      r'(\s+[^|$]+)?)')


class Pipeline(object):

    def __init__(self, plugins):
        """Initialize pipeline from plugin instances."""
        self.plugins = plugins
        self.started = False

    def validate(self):
        """Validate pipeline."""
        if len(self.plugins) == 0:
            raise ValueError("There is no plugins.")
        if not isinstance(self.plugins[0], BaseInput):
            raise ValueError("First plugin ought be an input plugin.")

    def start(self):
        """Start pipeline.

        This start each plugin in the pipeline. you can start a
        """
        if self.started:
            raise RuntimeError("You started this pipeline already.")
        for plugin in self.plugins:
            plugin.start()
        self.started = True

    def step(self):
        """Execute each plugin in the pipeline once."""
        if not self.started:
            raise RuntimeError("You can not step a pipeline without start it"
                               " first.")

    def stop(self):
        """Stop pipeline.

        This start each plugin in the pipeline. you can stop a
        pipeline only after start it
        """
        if not self.started:
            raise RuntimeError("You can not stop a pipeline without start it"
                               " first.")

        for plugin in self.plugins:
            plugin.stop()
        self.started = False

    def terminate(self):
        """Terminate pipeline.

        This procedure start each plugin in the pipeline.
        """
        for plugin in self.plugins:
            plugin.terminate()


def _parse_cmds(cmds):
    while cmds:
        match = cmd_ptrn.search(cmds)
        if match:
            cmd = match.group().strip()
            yield cmd
            endpos = match.span()[1]
            cmds = cmds[endpos + 1:]
        else:
            logging.error("Irregular command: '{}'".format(cmds))


def _create_plugin_from_cmd(cmd):
    elm = cmd.split()
    name = elm[0]
    mmap = swak.plugins.MODULE_MAP
    for pname in mmap.keys():
        if name == pname:
            sys.argv = elm
            plugin = mmap[name].main(standalone_mode=False)
            return plugin


def build_pipeline_from_cmds(cmds):
    """Build pipeline from command string.

    Build pipeline from parsed command.

    Returns:
        Pipeline:
    """
    plugins = []
    for cmd in _parse_cmds(cmds):
        plugin = _create_plugin_from_cmd(cmd)
        plugins.append(plugin)

    return Pipeline(plugins)
