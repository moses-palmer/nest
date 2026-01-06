"""The Package Manager for Everywhere.
"""

from .. import Twig, system


main = Twig.empty()

gcc = system.package(
    package='homebrew-gcc',
    description='GNU compiler collection.') \
    .depends(main)
binutils = system.package(
    package='homebrew-binutils',
    description='GNU binary tools for native development.') \
    .depends(main)
bison = system.package(
    package='homebrew-bison',
    description='Parser generator.') \
    .depends(main)
build_environment = Twig.empty('homebrew-build-environment') \
    .depends(gcc) \
    .depends(binutils) \
    .depends(bison) \
    .provides('build-environment')


@main.completer
def homebrew_completer(me: Twig):
    me.run('brew', 'update', '--quiet')
    me.run('brew', 'upgrade', '--quiet', '--yes')
