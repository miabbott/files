#!/usr/bin/env python3

# Scractch script to share Aliyun replicated images with accounts

import json
import logging as log
import requests
import subprocess
import sys

# see https://issues.redhat.com/browse/SPLAT-193 for account values
CI = "5920522175273455"
ALI = "1474626365013525"
DEV = "5807403157081522"
QE = "5724326381648897"


log.basicConfig(
    format='[%(levelname)s]: %(message)s',
    level=log.INFO)

cmd_out = subprocess.run(['aliyun', 'ecs', 'DescribeRegions'], capture_output=True, text=True)
regions_list = json.loads(cmd_out.stdout)['Regions']['Region']
endpoint_map = {}
for r in regions_list:
    endpoint_map[r['RegionId']] = r['RegionEndpoint']

# use any available meta.json URL for this. removed since it pointed to internal URL.
url = 'https://rhcos-redirector.apps.art.xq1c.p1.openshiftapps.com/art/storage/releases/rhcos-4.10/410.84.202112040202-0/x86_64/meta.json'
if len(sys.argv) > 1:
    url = sys.argv[1]

req = requests.get(url)
meta = req.json()

aliyun = meta['aliyun']

for item in aliyun:
    region = item['name']
    image = item['id']
    endpoint = endpoint_map[region]
    base_cmd = ['aliyun', '--endpoint', endpoint, 'ecs']
    # aliyun --profile rhcos-upload-amis ecs ModifyImageSharePermission --ImageId XXX --RegionId XXX --AddAccount.1 XXX
    share_cmd = base_cmd.copy() + ['ModifyImageSharePermission', '--ImageId', image, '--RegionId', region, '--IsPublic', 'true']
    log.info(f'Sharing image {image} in {region}')
    print(' '.join(share_cmd))
    command = subprocess.run(share_cmd, capture_output=True, text=True)
    if command.returncode != 0:
        print("Failed to share image")    # frustratingly the `aliyun` CLI returns error messages to stdout
        print(command.stdout)
        print(command.stderr)
