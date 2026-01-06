"""Configuration specific to macOS.
"""

from .. import Twig, homebrew, system


main = Twig.empty()

bash_completion = system.package(
    package='homebrew-bash-completion',
    description='Programmable completion for Bash.') \
    .depends(main)
coreutils = system.package(
    package='homebrew-coreutils',
    description='GNU File, Shell, and Text utilities.') \
    .depends(main)
gnu_sed = system.package(
    package='homebrew-gnu-sed',
    description='GNU implementation of the famous stream editor.') \
    .depends(main)
