"""Enables virtualisation and definition of local VMs.
"""

from pathlib import Path
from typing import Optional

from xml.etree import ElementTree as et

from nest.twigs import Twig, caller_context, empty, run, system, twig


main = empty()
daemon_driver_qemu = system.package(
    package='libvirt-daemon-driver-qemu',
    description='Virtualisation daemon QEMU connection driver.') \
    .depends(main)
daemon_system = system.package(
    package='libvirt-daemon-system',
    description='Libvirt daemon configuration files.') \
    .depends(main)
clients = system.package(
    package='libvirt-clients',
    description='Programs for the libvirt library.') \
    .depends(main)


def domain(
        *,
        name: Optional[str]=None,
        description: Optional[str]=None) -> Twig:
    """Defines a *libvirt domain* twig.

    :param name: The name of the domain. If not specified, the name of the
    calling module is used.

    :param description: A description of the domain. If not specified, the
    docstring of the calling module is used.

    :return: the twig
    """
    def domain_path(me: Twig) -> Path:
        return me.source.parent / 'domains'

    def domain_xml(me: Twig) -> Path:
        return domain_path(me) / '{}.xml'.format(me.name)

    def domain_name(me: Twig) -> str:
        return et.parse(domain_xml(me)).find('./name').text

    @twig(
        name=name,
        description=description,
        globals=caller_context())
    def main(me: Twig):
        run(
            me.name,
            'virsh', 'define', domain_xml(me),
            interactive=False)

    @main.checker
    def is_installed(me: Twig) -> bool:
        return run(
            me,
            'virsh', 'domstate', domain_name(me),
            check=True,
            silent=True)

    @main.remover
    def remove(me: Twig):
        if is_installed(me):
            run(
                me.name,
                'virsh', 'undefine', domain_name(me),
                interactive=False)

    return main
