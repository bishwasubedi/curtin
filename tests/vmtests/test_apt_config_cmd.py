""" test_apt_config_cmd
    Collection of tests for the apt configuration features when called via the
    apt-config standalone command.
"""
import textwrap

from . import VMBaseClass
from .releases import base_vm_classes as relbase


class TestAptConfigCMD(VMBaseClass):
    """TestAptConfigCMD - test standalone command"""
    conf_file = "examples/tests/apt_config_command.yaml"
    interactive = False
    extra_disks = []
    fstab_expected = {}
    disk_to_check = []
    collect_scripts = [textwrap.dedent("""
        cd OUTPUT_COLLECT_D
        cat /etc/fstab > fstab
        ls /dev/disk/by-dname > ls_dname
        find /etc/network/interfaces.d > find_interfacesd
        cp /etc/apt/sources.list.d/curtin-dev-ubuntu-test-archive-xenial.list .
        cp /etc/cloud/cloud.cfg.d/curtin-preserve-sources.cfg .
        apt-cache policy | grep proposed > proposed-enabled
        """)]

    def test_cmd_proposed_enabled(self):
        """check if proposed was enabled"""
        self.output_files_exist(["proposed-enabled"])
        self.check_file_regex("proposed-enabled",
                              r"500.*%s-proposed" % self.release)

    def test_cmd_ppa_enabled(self):
        """check if specified curtin-dev ppa was enabled"""
        self.output_files_exist(
            ["curtin-dev-ubuntu-test-archive-%s.list" % self.release])
        self.check_file_regex("curtin-dev-ubuntu-test-archive-%s.list" %
                              self.release,
                              (r"http://ppa.launchpad.net/"
                               r"curtin-dev/test-archive/ubuntu"
                               r" %s main" % self.release))

    def test_cmd_preserve_source(self):
        """check if cloud-init was prevented from overwriting"""
        self.output_files_exist(["curtin-preserve-sources.cfg"])
        self.check_file_regex("curtin-preserve-sources.cfg",
                              "apt_preserve_sources_list.*true")


class XenialTestAptConfigCMDCMD(relbase.xenial, TestAptConfigCMD):
    """ XenialTestAptSrcModifyCMD
        apt feature Test for Xenial using the standalone command
    """
    __test__ = True
