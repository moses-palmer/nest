"""Configuration specific to homebrew.
"""

from .. import Twig, system


main = Twig.empty()

bash_completion = system.package(
    package='bash-completion',
    description='Programmable completion for Bash')
