"""Find, Filter, Preview, Pick. All lua, all the time.
"""

from .. import Twig, build_environment, nvim


main = nvim.plugin()


@main.completer
def complete(me: Twig):
    source_dir = me.source / '.config' / 'nvim' / 'pack' / 'nvim' / 'start' \
        / 'telescope-fzf-native.nvim'
    build_dir = source_dir / 'build'
    if not build_dir.is_dir() \
            or not any('fzf' in p.name for p in build_dir.iterdir()):
        me.run(
            'make', '--directory=${source_dir}',
            source_dir=source_dir)
