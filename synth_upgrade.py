# Check status for the checksum of the booted tree and Compare
# to new 'noop' base ref_spec
# If it matches, create a second 'noop' tree based on the current
# tree to use as an upgrade target, and upgrade

import json
import subprocess

ref_spec = "synth_test"
target_id = ""
tree_id = ""

atomic_status = subprocess.check_output(['atomic', 'host', 'status', '--json'])

data = json.loads(atomic_status)

for r in data['deployments']:
    if r['booted'] is True:
        tree_id=r['checksum']

with open("target_commit.txt", "r")as text_file:
    target_id = text_file.read()

if tree_id == target_id.rstrip():
    upgrade_tree = subprocess.check_output(["sudo", "ostree", "commit", "-b", ref_spec, "--tree=ref=%s" % ref_spec])
    with open("target_upgrade.txt", "w")as text_file:
        text_file.write(upgrade_tree.rstrip())
    atomic_upgrade = subprocess.check_output(['sudo', 'atomic', 'host', 'upgrade'])
else:
    exit(1)
