"""A PDF viewer controllable by D-BUS.
"""

from .. import Twig, system


main = Twig.empty()
pythoin_gi_cairo = system.package(
    package='python-gi-cairo',
    description='Python 3 Cairo bindings.') \
    .depends(main)
libpoppler_glib = system.package(
    package='libpoppler-glib',
    description='PDF rendering library.') \
    .depends(main)
