# Check status for the checksum of the booted tree and Compare
# to new 'noop' base ref_spec
# If it matches, create a second 'noop' tree based on the current
# tree to use as an upgrade target, and upgrade

import json
import subprocess

ref_spec = "synth_test"
target_id = ""
deploy_id = ""

atomic_status = subprocess.check_output(['atomic', 'host', 'status', '--json'])

data = json.loads(atomic_status)

for r in data['deployments']:
    if r['booted'] is True:
        deploy_id=r['checksum']

with open("target_commit.txt", "r")as text_file:
    target_id = text_file.read()

if deploy_id == target_id.rstrip():
    atomic_upgrade = subprocess.check_output(['sudo', 'atomic', 'host', 'upgrade'])
else:
    print "Booted tree checksum %s doesn't match target tree id %s -- setup failed" % (deploy_id, target_id)
    exit(1)
