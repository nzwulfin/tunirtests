import unittest
import os
import re
import time
from .testutils import system, if_atomic, if_upgrade, if_rollback


@unittest.skipUnless(if_atomic(), "It's not an atomic image")
class TestAtomicFirstBootRun(unittest.TestCase):

    def test_docker_image_run(self):
        out, err, eid = system(
            'docker run --rm busybox true && echo "PASS"')
        out = out.decode('utf-8')
        self.assertEqual('PASS\n', out)


@unittest.skipUnless(if_atomic(), "It's not an Atomic image")
class TestDockerStorageSetup(unittest.TestCase):

    def test_journalctl_logs(self):
        """Test journalctl logs for docker-storage-setup"""
        out, err, eid = system(
            'journalctl -o cat --unit docker-storage-setup.service'
        )
        out = out.decode('utf-8')
        print(repr(out))
        self.assertTrue(
            'Started Docker Storage Setup.' in out, out
        )

    def test_lsblk_output(self):
        """Test output for lsblk"""
        out, err, eid = system('sudo lsblk')
        out = out.decode('utf-8')
        self.assertTrue(
            re.search(r'atomicos-root.*\d+(?:.\d+)?G.*lvm.*/sysroot.*\n', out)
        )
        self.assertTrue(
            re.search(r'atomicos-docker--pool_tmeta.*\d+(?:.\d+)?M.*lvm', out)
        )
        self.assertTrue(
            re.search(r'atomicos-docker--pool_tdata.*\d+(?:.\d+)?G.*lvm', out)
        )


@unittest.skipUnless(if_atomic(), "It's not an Atomic image")
class TestDockerInstalled(unittest.TestCase):

    def test_run(self):
        out, err, eid = system('rpm -q docker')
        out = out.decode('utf-8')
        self.assertFalse('not installed' in out, out)


@unittest.skipUnless(if_atomic(), "It's not an Atomic image")
@unittest.skipUnless(if_upgrade(), "No upgrade is available for this Atomic host")
class TestAtomicUpgradeRun(unittest.TestCase):

    def test_upgrade_run(self):
        # We create a file /etc/file1 before running an upgrade.
        # This file should persist, even after rolling back the upgrade.
        # This we assert in
        # TestAtomicRollbackPostReboot.test_atomic_rollback_post_reboot
        with open('/etc/file1', 'w') as f:
            f.write('1\n')
            f.close

        out, err, eid = system('sudo atomic host upgrade')
        err = err.decode('utf-8')
        # Assert successful run
        print(out, err)
        self.assertFalse(err)
        time.sleep(30)


@unittest.skipUnless(if_atomic(), "It's not an Atomic image")
@unittest.skipUnless(if_rollback(), "No rollback is available for this Atomic host")
class TestAtomicUpgradePostReboot(unittest.TestCase):

    def test_upgrade_post_reboot(self):
        out, err, eid = system(
            'docker run --rm busybox true && echo "PASS"')
        out = out.decode('utf-8')
        self.assertEqual('PASS\n', out)


@unittest.skipUnless(if_atomic(), "It's not an Atomic image")
@unittest.skipUnless(if_rollback(), "No rollback is available for this Atomic host")
class TestAtomicRollbackRun(unittest.TestCase):

    def test_atomic_rollback_run(self):
        # We make changes to the system by creating /etc/file2 before
        # running rollback. Once rollback is run, /etc/file2 will be
        # removed. We assert that in the following test case.
        with open('/etc/file2', 'w') as f:
            f.write('2\n')
            f.close

        out, err, eid = system('sudo atomic host rollback')
        err = err.decode('utf-8')
        self.assertFalse(err)
        print(out, err)
        time.sleep(30)


@unittest.skipUnless(if_atomic(), "It's not an Atomic image")
@unittest.skipUnless(if_rollback(), "No rollback is available for this Atomic host")
class TestAtomicRollbackPostReboot(unittest.TestCase):

    def test_atomic_rollback_post_reboot(self):
        out, err, eid = system('atomic host status')
        out = out.decode('utf-8')
        self.assertTrue(out)

        # Assert that file1 is present
        self.assertTrue(os.path.isfile('/etc/file1'))

        # Assert that file2 is not present
        self.assertFalse(os.path.isfile('/etc/file2'))

        # Assert that running busybox docker image works after rollback
        out, err, eid = system(
            'docker run --rm busybox true && echo "PASS"')
        out = out.decode('utf-8')
        self.assertEqual(out, 'PASS\n')


@unittest.skipUnless(if_atomic(), "It's not an Atomic image")
class TestAtomicDockerImage(unittest.TestCase):

    def test_docker_image(self):
        out, err, eid = system('sudo docker pull fedora:latest')
        self.assertFalse(err)
        time.sleep(10)
        out, err, eid = system(
            'sudo docker run --rm fedora:latest '
            'true && echo "PASS" || echo "FAIL"')
        out = out.decode('utf-8')
        self.assertEqual(out, 'PASS\n')

@unittest.skipUnless(if_atomic(), "It's not an Atomic image")
class TestAtomicCommand(unittest.TestCase):

    def test_atomic_command(self):
        out, err, eid = system('atomic run kushaldas/busybox')
        self.assertEqual(eid, 0, out+err)

# https://github.com/kushaldas/tunirtests/issues/8
@unittest.skipUnless(if_atomic(), "It's not an Atomic image")
class TestRootMount(unittest.TestCase):

    def test_root_mount(self):
        out, err, eid = system('docker run --rm -v /:/host busybox')
        self.assertEqual(eid, 0, out+err)

@unittest.skipUnless(if_atomic(), "It's not an Atomic image")
class Testreadonlymount(unittest.TestCase):

    def test_read_only(self):
        "Tests the read only dirs."
        dirs = [ '/bin/','/sbin/', '/usr/']
        for d in dirs:
            with self.assertRaises(OSError):
                with open(os.path.join(d, 'hooha.txt'), 'w') as fobj:
                    fobj.write('hello.')

@unittest.skipUnless(if_atomic(), "It's not an Atomic image")
class TestDockerDaemon(unittest.TestCase):

    def test_docker(self):
        out, err, eid = system('docker run --rm  --privileged -v /run:/run -v /:/host --net=host --entrypoint=/bin/bash fedora:23 -c "chroot /host/ docker version"')
        self.assertEqual(eid, 0, out+err)
        out = out.decode('utf-8')
        self.assertIn('Server:\n Version', out)

@unittest.skipUnless(if_atomic(), "It's not an Atomic image")
class TestUpgrade(unittest.TestCase):

    def setup(self):
        # Compare the checksum of the booted tree against the stored checksum
        # of the locally created 'noop' upgrade tree
        # If passed upgrade, test the booted tree matches the 'noop' upgrade tree

        import json
        import subprocess

        target_id = ""
        deploy_id = ""
        id_source = "synth_upgrade.txt"

        # Read the status output to determine trees booted and deployed
        atomic_status = subprocess.check_output(['atomic', 'host', 'status', '--json'])
        data = json.loads(atomic_status)

        for r in data['deployments']:
            if r['booted'] is True:
                self.deploy_id=r['checksum']

        with open(id_source, "r")as text_file:
            self.target_id = text_file.read()

    def test_upgrade(self):
        self.assertEqual(self.target_id, self.deploy_id)

@unittest.skipUnless(if_atomic(), "It's not an Atomic image")
class TestRollback(unittest.TestCase):

    def setup(self):
        # Compare the checksum of the booted tree against the stored checksum
        # of the locally created 'noop' tree
        # Used to sanity check inital setup of 'noop' tree
        # If passed rollback, test the booted tree matches the original 'noop' tree

        import json
        import subprocess

        id_source = "synth_origin.txt"

        # Read the status output to determine trees booted and deployed
        atomic_status = subprocess.check_output(['atomic', 'host', 'status', '--json'])
        data = json.loads(atomic_status)

        for r in data['deployments']:
            if r['booted'] is True:
                self.deploy_id=r['checksum']

        with open(id_source, "r")as text_file:
            self.target_id = text_file.read()

    def test_upgrade(self):
        self.assertEqual(self.target_id, self.deploy_id)


if __name__ == '__main__':
    unittest.main()
