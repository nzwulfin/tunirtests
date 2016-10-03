# Setup up a local 'noop' branch and deploy as the new based
# This allows for additional 'noop' upgrade targets to test
# the upgrade and rollback capability of the current tree
# Dump the checksum of the new tree ref to a file for later

import json
import subprocess

tree = ""
ref_spec = "synth_test"

atomic_status = subprocess.check_output(['atomic', 'host', 'status', '--json'])

data = json.loads(atomic_status)

for r in data['deployments']:
    if r['booted'] is True:
        tree=r['origin']

synthetic = subprocess.check_output(["sudo", "ostree", "commit", "-b", ref_spec, "--tree=ref=%s" % tree])

with open("synth_origin.txt", "w")as text_file:
    text_file.write(synthetic.rstrip())

deploy = subprocess.check_output(["sudo", "ostree", "admin", "deploy", ref_spec])

upgrade_tree = subprocess.check_output(["sudo", "ostree", "commit", "-b", ref_spec, "--tree=ref=%s" % ref_spec])

with open("synth_upgrade.txt", "w")as text_file:
    text_file.write(upgrade_tree.rstrip())
