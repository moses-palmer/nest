"""A terminal overlay controlled by D-BUS.
"""

import re

from .. import Twig, dconf, dbus_send, nerdfont


main = dconf.keybindings(
    dconf.KeyBinding(
        name='\'Toggle Terminal Overlay\'',
        binding='\'<Primary>section\'',
        command='\'dbus-send '
            '--session '
            '--dest=com.newrainsoftware.TerminalOverlay '
            '--type=method_call '
            '/com/newrainsoftware/TerminalOverlay '
            'com.newrainsoftware.TerminalOverlay.Toggle\''),
    dconf.KeyBinding(
        name='\'Cycle Terminal Overlay Monitor\'',
        binding='\'<Primary>Tab\'',
        command='\'dbus-send '
            '--session '
            '--dest=com.newrainsoftware.TerminalOverlay '
            '--type=method_call '
            '/com/newrainsoftware/TerminalOverlay '
            'com.newrainsoftware.TerminalOverlay.CycleDisplay\''))
