#!/usr/bin/env python3

# Verifies that images on Aliyun are marked as publicly available given a
# `meta.json` from coreos-assembler

import subprocess
import json
import logging as log

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

aliyun = meta['aliyun']

for item in aliyun:
    region = item['name']
    image = item['id']
    endpoint = endpoint_map[region]
    base_cmd = ['aliyun', '--endpoint', endpoint, 'ecs']

    log.info(f"Getting info about {image} in region {region}")
    describe_cmd = base_cmd.copy() + ['DescribeImages', '--RegionId', region, '--ImageId', image]
    desc_out = subprocess.run(describe_cmd, capture_output=True, text=True)
    desc_json = json.loads(desc_out.stdout)
    if desc_json['TotalCount'] == 0:
        log.info(f"Image {image} not present in {region}")
        continue

    if not desc_json['Images']['Image'][0]['IsPublic']:
        log.info(f"Image {image} in region {region} is not public!")