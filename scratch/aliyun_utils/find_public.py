#!/usr/bin/env python3

#

import json
import requests
import subprocess
import sys


cmd_out = subprocess.run(['aliyun', 'ecs', 'DescribeRegions'], capture_output=True, text=True)
regions_list = json.loads(cmd_out.stdout)['Regions']['Region']
endpoint_map = {}
for r in regions_list:
    endpoint_map[r['RegionId']] = r['RegionEndpoint']

for region in endpoint_map:
    print(f"Checking region {region}")
    endpoint = endpoint_map[region]
    base_cmd = ['aliyun', '--endpoint', endpoint, 'ecs']
    check_desc_cmd = base_cmd.copy() + ['DescribeImages', '--RegionId', region, '--PageSize', '100', '--ImageOwnerAlias', 'self']
    check_desc_out = subprocess.run(check_desc_cmd, capture_output=True, text=True)
    if check_desc_out.returncode != 0:
        print(f"FAIL: Failed to get images in {region}")
        print(check_desc_out.stderr)
        continue
    check_desc_json = json.loads(check_desc_out.stdout)
    if check_desc_json['TotalCount'] == 0:
        print(f"FAIL: No images in {region}")
        continue

    for image in check_desc_json['Images']['Image']:
        imageid = image['ImageId']
        if image['IsPublic']:
            print(f"Marking {imageid} in {region} as private")
            share_cmd = base_cmd.copy() + ['ModifyImageSharePermission', '--ImageId', imageid, '--RegionId', region, '--IsPublic', 'false']
            share_cmd_out = subprocess.run(share_cmd, capture_output=True, text=True)
            if share_cmd_out.returncode != 0:
                print("Failed to share image")    # frustratingly the `aliyun` CLI returns error messages to stdout
                print(share_cmd_out.stdout)
                print(share_cmd_out.stderr)
