# Compare the checksum of the booted tree against the stored checksum
# of the locally created 'noop' upgrade tree
# If it matches, trigger the rollback

import json
import subprocess

ref_spec = "synth_test"
target_id = ""
tree_id = ""

atomic_status = subprocess.check_output(['atomic', 'host', 'status', '--json'])

data = json.loads(atomic_status)

for r in data['deployments']:
    if r['booted'] is True:
        deploy_id=r['checksum']

with open("target_upgrade.txt", "r")as text_file:
    target_id = text_file.read()

if deploy_id == target_id.rstrip():
    atomic_rollback = subprocess.check_output(['sudo', 'atomic', 'host', 'rollback'])
else:
    print "Booted tree checksum %s doesn't match upgrade target tree id %s -- upgrade failed" % (deploy_id, target_id)
    exit(1)
