# Configuration file for ipython.

c = get_config()


## Whether to display a banner upon starting IPython.
#  Default: True
c.TerminalIPythonApp.display_banner = False

## Shortcut style to use at the prompt. 'vi' or 'emacs'.
#  Default: 'emacs'
c.TerminalInteractiveShell.editing_mode = 'vi'

## Set to confirm when you try to exit IPython with an EOF (Control-D in Unix,
#  Control-Z/Enter in Windows). By typing 'exit' or 'quit', you can force a
#  direct exit without any confirmation.
#  Default: True
c.TerminalInteractiveShell.confirm_exit = False
