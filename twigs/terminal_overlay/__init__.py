"""A terminal overlay controlled by D-BUS.
"""

import re

from .. import Twig, dbus_send, dconf, gi_cairo, libpoppler_glib, twig


#: The path to custom key bindings.
PATH = '/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings'

#: The regular expression matching custom bindings.
CUSTOM_BINDING_RE = re.compile(r'custom([0-9]+)')

#: The bindings.
BINDINGS = [
    {
        'name': '\'Toggle Terminal Overlay\'',
        'binding': '\'<Primary>section\'',
        'command': '\'dbus-send '
            '--session '
            '--dest=com.newrainsoftware.TerminalOverlay '
            '--type=method_call '
            '/com/newrainsoftware/TerminalOverlay '
            'com.newrainsoftware.TerminalOverlay.Toggle\''},
    {
        'name': '\'Cycle Terminal Overlay Monitor\'',
        'binding': '\'<Primary>Tab\'',
        'command': '\'dbus-send '
            '--session '
            '--dest=com.newrainsoftware.TerminalOverlay '
            '--type=method_call '
            '/com/newrainsoftware/TerminalOverlay '
            'com.newrainsoftware.TerminalOverlay.CycleDisplay\''}]


@twig()
def main(me: Twig):
    next_index = max(
        (
            int(CUSTOM_BINDING_RE.match(binding).group(1))
            for binding in dconf.list(me, '{}/'.format(PATH))
            if CUSTOM_BINDING_RE.match(binding)),
        default=0) + 1
    for binding in _list_missing(me):
        base = '{}/custom{}'.format(PATH, next_index)
        for name, value in binding.items():
            dconf.write(me, '{}/{}'.format(base, name), value)
        next_index += 1


@main.checker
def is_installed(me: Twig):
    return len(_list_missing(me)) == 0


@main.remover
def remove(me: Twig):
    for item in dconf.list(me, '{}/'.format(PATH)):
        path = '{}/{}'.format(PATH, item)
        name = dconf.read(me, '{}name'.format(path))
        if any(name == binding['name'] for binding in BINDINGS):
            dconf.reset(me, path)


def _list_missing(me: Twig) -> [dict]:
    """Lists missing key bindings.
    """
    current_names = [
        dconf.read(me, '{}/{}name'.format(PATH, binding))
        for binding in dconf.list(me, '{}/'.format(PATH))]
    return [
        binding
        for binding in BINDINGS
        if binding['name'] not in current_names]
