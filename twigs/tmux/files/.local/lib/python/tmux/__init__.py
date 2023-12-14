import subprocess
import sys

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator, Optional, Union, TypeVar, Generic


#: The tmux binary name.
BIN = 'tmux'

# Forward declare types for older versions of Python
try:

    def __t() -> Server:
        pass

    del __t
except NameError:
    Server = 'Server'
    Session = 'Session'
    Window = 'Window'
    Pane = 'Pane'


class Options:
    """The options for a part of tmux: servers, sessions, windows or panes."""

    class Type(Enum):
        """The type of an option collection."""

        SERVER = ('-s',)
        SESSION = ()
        PANE = ('-p',)
        WINDOW = ('-w',)

    def __init__(self, server: Server, type: Type, target: Optional[str]):
        self._server = server
        if target is not None:
            self._specifier = tuple(list(type.value) + ['-t', target])
        else:
            self._specifier = type.value

    @property
    def server(self) -> Server:
        """The server."""
        return self._server

    def __getitem__(self, key: str) -> str:
        try:
            return self._server._tmux(
                'show-options', '-v', *self._specifier, key
            ).strip()
        except subprocess.CalledProcessError as e:
            raise KeyError(key)

    def __setitem__(self, key: str, value: str):
        return self.server._tmux(
            'set-option', *self._specifier, key, value
        ).strip()

    def __iter__(self) -> Iterator[str]:
        return (
            line.strip().split(maxsplit=1)[0]
            for line in self.server._tmux(
                'show-options',
                *self._specifier,
            ).splitlines()
            if line.strip()
        )


class Base:
    """A tmux base item."""

    #: The type of the options.
    _OPTION_TYPE: Options.Type

    @property
    @lru_cache
    def server(self) -> Server:
        """The tmux server owning this item."""
        raise NotImplementedError()

    @property
    @lru_cache
    def options(self) -> Options:
        """The options of this item."""
        return Options(self.server, self._OPTION_TYPE, self._option_target())

    def _option_target(self) -> Optional[str]:
        """The target used to retrieve the specific options."""
        raise NotImplementedError()


P = TypeVar('P', bound=Base)


class Visual(Base, Generic[P]):
    """A visual part of tmux."""

    #: The command used to select this item.
    _SELECT_COMMAND = ''

    #: The command used to kill this item.
    _KILL_COMMAND = ''

    def __init__(self, parent: P, id: str):
        self._parent = parent
        self._id = id

    def __str__(self):
        return f'{self.__class__.__name__}:{self.path}'

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def _option_target(self) -> Optional[str]:
        return self._id

    @property
    def server(self) -> Server:
        if isinstance(self._parent, Server):
            return self.parent
        else:
            return self._parent.server

    @property
    def exists(self) -> bool:
        """Whether this item exists."""
        try:
            self.server._tmux('has-session', '-t', self.id)
            return True
        except subprocess.CalledProcessError:
            return False

    @property
    def id(self) -> str:
        """The ID of this item."""
        return self._id

    @property
    def path(self) -> str:
        """The full ID path of this item."""
        if not isinstance(self._parent, Server):
            return f'{self._parent.id}:{self._id}'
        else:
            return self._id

    @property
    def parent(self) -> P:
        """The parent of this item."""
        return self._parent

    @property
    def active(self) -> bool:
        """Whether this item is active."""
        match self._parent:
            case Server():
                return self._parent.current_session == self
            case Container():
                return self._parent._current_child() == self.id

    def activate(self):
        """Activates this item."""
        self.server._tmux(self._SELECT_COMMAND, '-t', self.id)

    def kill(self):
        """Kills this part."""
        self.server._tmux(self._KILL_COMMAND, '-t', self.id)


C = TypeVar('C', bound=Visual)


class Container(Generic[C]):
    #: The format used to show children.
    _CHILD_PROPERTY: str

    #: The format used to show children.
    _CHILD_COMMAND: str

    #: The path in the visual tree of this container, if any.
    path: Optional[str]

    #: The tmux server.
    server: Server

    def __iter__(self) -> Iterator[Visual]:
        raise NotImplementedError()

    def child(self, id: str) -> Optional[C]:
        """Acquires a reference to an existing child of this container.

        :param id: The ID of the child.
        :return: a reference to the child, if the child exists
        """
        result = self._child(id)
        if result.exists:
            return result
        else:
            return None

    def _child(self, id: str) -> C:
        raise NotImplementedError()

    def _current_child(self) -> Optional[str]:
        """The current active child of this container."""
        return self.server._format(self._CHILD_PROPERTY, self.path)

    def _children(self) -> Iterator[str]:
        """The children of this container."""
        if self.path is not None:
            args = (
                self._CHILD_COMMAND,
                '-t',
                self.path,
                '-F',
                self._CHILD_PROPERTY,
            )
        else:
            args = (self._CHILD_COMMAND, '-F', self._CHILD_PROPERTY)
        return (
            line.strip()
            for line in self.server._tmux(*args).splitlines()
            if line.strip()
        )


class Server(Base, Container['Session']):
    """The tmux server.

    All commands go through this instance.
    """

    _OPTION_TYPE = Options.Type.SERVER
    _CHILD_PROPERTY = '#{session_id}'
    _CHILD_COMMAND = 'list-sessions'

    def __init__(self):
        self._encoding = sys.stdout.encoding
        self.path = None

    def _option_target(self) -> Optional[str]:
        return None

    def __iter__(self) -> Iterator[Visual]:
        return self.sessions

    def _tmux(self, *args: str) -> str:
        return subprocess.check_output(
            [BIN] + list(args),
            stderr=subprocess.DEVNULL,
        ).decode(self._encoding)

    def _format(self, s: str, target: Optional[str] = None) -> str:
        if target is not None:
            return self._tmux('display-message', '-p', '-t', target, s).strip()
        else:
            return self._tmux('display-message', '-p', s).strip()

    def _child(self, id: str) -> Session:
        return Session(self, id)

    @property
    def server(self) -> Server:
        return self

    @property
    def current_session(self) -> Optional[Session]:
        """The current session."""
        i = self._current_child()
        if i:
            return Session(self, i)
        else:
            return None

    @current_session.setter
    def current_session(self, value: Union[Session, str]):
        match value:
            case Session():
                self.current_session = value.id
            case str():
                self.server._tmux('attach-session', '-t', value)

    @property
    def sessions(self) -> Iterator[Session]:
        """The session."""
        return (Session(self, i) for i in self._children())

    def new_session(
        self,
        name: Optional[str] = None,
        cwd: Optional[Path] = None,
        **env: str,
    ) -> Session:
        """Creates a new session.

        :param name: The session name.
        :param cwd: The CWD of the session.
        :param env: Environment variables for the session.
        """
        return self._child(
            self._tmux(
                'new-session',
                '-P',
                '-F',
                '#{session_id}',
                *self._args(name, cwd, env),
            ).strip()
        )

    def notify(self, message: str):
        """Displays a quick notification.

        :param message: The message to display.
        """
        self._tmux('display-message', message)

    def query(
        self, prompt: str, *alternatives: str, width: Optional[int] = None
    ) -> str:
        """Performs a modal query.

        :param prompt: The main prompt.
        :param alternatives: The alternatives presented.
        :param width: The width of the window.
        """
        command = ['tmux-query', '--prompt', prompt]
        if width is not None:
            command += ['--width', str(width)]
        return (
            subprocess.check_output(command + list(alternatives))
            .decode(self._encoding)
            .strip()
        )

    def _args(
        self,
        name: Optional[str],
        cwd: Optional[Path] = None,
        env: Optional[dict[str, str]] = None,
    ) -> list[str]:
        args = []
        if name is not None:
            args += ['-n', name]
        if cwd is not None:
            args += ['-c', str(cwd)]
        if env is not None:
            args += _env(**env)
        return args


class Session(Visual[Server], Container['Window']):
    """A tmux session.

    A session is a collection of windows.
    """

    _SELECT_COMMAND = 'attach-session'
    _KILL_COMMAND = 'kill-session'
    _OPTION_TYPE = Options.Type.SESSION
    _CHILD_PROPERTY = '#{window_id}'
    _CHILD_COMMAND = 'list-windows'

    def _child(self, id: str) -> Window:
        return Window(self, id)

    @property
    def current_window(self) -> Optional[Window]:
        """The current window of this session."""
        i = self._current_child()
        if i:
            return Window(self, i)
        else:
            return None

    @current_window.setter
    def current_window(self, value: Union[Window, str]):
        match value:
            case Window():
                self.current_window = value.id
            case str():
                self.server._tmux('select-window', '-t', value)
            case _:
                raise ValueError(value)

    @property
    def windows(self) -> Iterator[Window]:
        """The windows of this session."""
        return (Window(self, i) for i in self._children())

    def new_window(
        self,
        name: Optional[str] = None,
        cwd: Optional[Path] = None,
        **env: str,
    ) -> Window:
        """Creates a new window.

        :param name: The window name.
        :param cwd: The CWD of the window.
        :param env: Environment variables for the window.
        """
        return self._child(
            self.server._tmux(
                'new-window',
                '-P',
                '-F',
                '#{window_id}',
                *self._args(name, cwd, env),
            ).strip()
        )

    @property
    def name(self) -> str:
        """The name of this session."""
        return self.server._format('#{session_name}')

    @name.setter
    def name(self, value: str):
        self.server._tmux('rename-session', '-t', self.id, value)

    def __iter__(self) -> Iterator[Window]:
        return self.windows

    def _args(
        self,
        name: Optional[str],
        cwd: Optional[Path] = None,
        env: Optional[dict[str, str]] = None,
    ) -> list[str]:
        args = ['-t', self.id]
        if name is not None:
            args += ['-n', name]
        if cwd is not None:
            args += ['-c', str(cwd)]
        if env is not None:
            args += _env(**env)
        return args


class Window(Visual[Session], Container['Pane']):
    """A tmux window.

    A window is a collection of panes.
    """

    _SELECT_COMMAND = 'select-window'
    _KILL_COMMAND = 'kill-window'
    _OPTION_TYPE = Options.Type.WINDOW
    _CHILD_PROPERTY = '#{pane_id}'
    _CHILD_COMMAND = 'list-panes'

    class PresetLayout(Enum):
        """A preset layout for the panes in this window."""

        #: Panes are spread out evenly from left to right across the window.
        EVEN_HORIZONTAL = 'even-horizontal'

        #: Panes are spread evenly from top to bottom.
        EVEN_VERTICAL = 'even-vertical'

        #: A large (main) pane is shown at the top of the window and the
        #: remaining panes are spread from left to right in the leftover space
        #: at the bottom. Use the main-pane-height window option to specify the
        #: height of the top pane.
        MAIN_HORIZONTAL = 'main-horizontal'

        #: The same as main-horizontal but mirrored so the main pane is at the
        #: bottom of the window.
        MAIN_HORIZONTAL_MIRRORED = 'main-horizontal-mirrored'

        #: A large (main) pane is shown on the left of the window and the
        #: remaining panes are spread from top to bottom in the leftover space
        #: on the right. Use the main-pane-width window option to specify the
        #: width of the left pane.
        MAIN_VERTICAL = 'main-vertical'

        #: The same as main-vertical but mirrored so the main pane is on the
        #: right of the window.
        MAIN_VERTICAL_MIRRORED = 'main-vertical-mirrored'

        #: Panes are spread out as evenly as possible over the window in both
        #: rows and columns.
        TILED = 'tiled '

    def _child(self, id: str) -> Pane:
        return Pane(self, id)

    @property
    def session(self) -> Session:
        """The session owning this window."""
        return self._parent

    @property
    def current_pane(self) -> Optional[Pane]:
        """The current pane of this window."""
        i = self._current_child()
        if i:
            return Pane(self, i)
        else:
            return None

    @current_pane.setter
    def current_pane(self, value: Union[Pane, str]):
        match value:
            case Window():
                self.current_pane = value.id
            case str():
                self.server._tmux('select-pane', '-t', value)
            case _:
                raise ValueError(value)

    @property
    def panes(self) -> Iterator[Pane]:
        """The panes of this window."""
        return (Pane(self, i) for i in self._children())

    @property
    def name(self) -> str:
        """The name of this session."""
        return self.server._format('#{window_name}')

    @name.setter
    def name(self, value: str):
        self.server._tmux('rename-window', '-t', self.id, value)

    def apply_layout(self, layout: PresetLayout):
        """Applies a pre-defined layout.

        :param layout: The layout to use.
        """
        self.server._tmux('select-layout', '-t', self.id, layout.value)

    def __iter__(self) -> Iterator[Pane]:
        return self.panes


class Pane(Visual[Window]):
    """A tmux pane.
    A pane contains an output such as a terminal."""

    _SELECT_COMMAND = 'select-pane'
    _KILL_COMMAND = 'kill-pane'
    _OPTION_TYPE = Options.Type.PANE

    class Split(Enum):
        """The kinds of splits for a pane."""

        #: A horisontal split.
        HORIZONTAL = '-h'

        #: A vertical split.
        VERTICAL = '-v'

        def __invert__(self):
            return {
                self.HORIZONTAL: self.VERTICAL,
                self.VERTICAL: self.HORIZONTAL,
            }[self]

    class Order(Enum):
        """The order of the resulting panes after a split."""

        #: The new pane is placed before the current one.
        BEFORE = ['-b']

        #: The new pane is placed after the current one.
        AFTER = []

        def __invert__(self):
            return {
                self.AFTER: self.BEFORE,
                self.BEFORE: self.AFTER,
            }[self]

    @property
    def session(self) -> Session:
        """The session owning this pane."""
        return self.window.session

    @property
    def window(self) -> Window:
        """The window owning this pane."""
        return self._parent

    def respawn(
        self,
        command: list[str],
        cwd: Optional[Path] = None,
        **env: str,
    ):
        """Respawn this pane with a new command.

        :param command: The new command.
        :param cwd: The new CWD.
        :param env: The new environment overrides.
        """
        self.server._tmux(
            'respawn-pane', '-k', *self._args(command, None, False, cwd, env)
        )

    def split(
        self,
        split: Split,
        order: Order,
        command: list[str],
        size: Optional[str] = None,
        full: bool = False,
        cwd: Optional[Path] = None,
        **env: str,
    ) -> Pane:
        """Splits this pane into two.

        :param split: The kind of split to make.
        :param order: The order of the new pane.
        :param command: The new command.
        :param size: The size of the new pane.
        :param full: Whether to give the pane the full extents of the window
        instead of just splitting this pane.
        :param cwd: The new CWD.
        :param env: The new environment overrides.
        """
        return Pane(
            self.parent,
            self.server._tmux(
                'split-window',
                '-d',
                '-P',
                '-F',
                '#{pane_id}',
                split.value,
                *(order.value + self._args(command, size, full, cwd, env)),
            ).strip(),
        )

    def _args(
        self,
        command: list[str],
        size: Optional[str],
        full: bool,
        cwd: Optional[Path],
        env: Optional[dict[str, str]],
    ) -> list[str]:
        args = ['-t', self.id]
        if size is not None:
            args += ['-l', size]
        if full:
            args += ['-f']
        if cwd is not None:
            args += ['-c', str(cwd)]
        if env is not None:
            args += _env(**env)
        return args + command


def _env(**env: str) -> list[str]:
    return [
        a for e in (('-e', f'{k}={v}') for (k, v) in env.items()) for a in e
    ]
