#!/usr/bin/env python3

# Can be used to remove a number of images from Aliyun given a `meta.json` from
# coreos-assembler

import subprocess
import json
import logging as log
import sys

log.basicConfig(
    format='[%(levelname)s]: %(message)s',
    level=log.INFO)

cmd_out = subprocess.run(['aliyun', 'ecs', 'DescribeRegions'], capture_output=True, text=True)
regions_list = json.loads(cmd_out.stdout)['Regions']['Region']
endpoint_map = {}
for r in regions_list:
    endpoint_map[r['RegionId']] = r['RegionEndpoint']

with open("builds/latest/x86_64/meta.json", 'r') as f:
    meta = json.load(f)

if 'aliyun' not in meta.keys():
    log.info('Aliyun images already removed')
    sys.exit()

aliyun = meta['aliyun']

for item in aliyun:
    region = item['name']
    image = item['id']
    endpoint = endpoint_map[region]
    base_cmd = ['aliyun', '--endpoint', endpoint, 'ecs']

    # skip us-east-1
    if region == "us-east-1":
        continue

    log.info(f"Getting info about {image} in {region}")
    describe_cmd = base_cmd.copy() + ['DescribeImages', '--RegionId', region, '--ImageId', image]
    desc_out = subprocess.run(describe_cmd, capture_output=True, text=True)
    desc_json = json.loads(desc_out.stdout)
    if desc_json['TotalCount'] == 0:
        log.info(f"Image {image} not present in {region}")
        continue

    if desc_json['Images']['Image'][0]['IsPublic']:
        log.info(f"Setting public to false on {image}")
        modify_cmd = base_cmd.copy() + ['ModifyImageSharePermission', '--IsPublic', 'false', '--RegionId', region, '--ImageId', image]
        modify_out = subprocess.run(modify_cmd, capture_output=True, text=True)
        if modify_out.returncode != 0:
            raise Exception(f"Failed to mark image {image} in region {region} as not public")

    log.info(f"Deleting image {image}")
    delete_cmd = base_cmd.copy() + ['DeleteImage', '--RegionId', region, '--ImageId', image]
    delete_out = subprocess.run(delete_cmd, capture_output=True, text=True)
    if delete_out.returncode != 0:
        log.info(delete_out.stderr)
        raise Exception(f"Failed to delete image {image} in region {region}")

meta.pop('aliyun')
with open("builds/latest/x86_64/meta.json", 'w') as f:
     json.dump(meta, f)
