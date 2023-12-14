"""The Microsoft Java Debugger.
"""

import json
import os

from .. import Twig, jdtls, maven


main = maven.module(
    group='com.microsoft.java',
    artifact='com.microsoft.java.debug.plugin',
    target_format=str(
        jdtls.PLUGINS_DIR / 'com.microsoft.java.debug.plugin-{}.jar'))
