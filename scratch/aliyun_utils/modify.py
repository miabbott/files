#!/usr/bin/env python3

# Modifies Aliyun images to have name + description

import json
from tabnanny import check
import requests
import subprocess
import sys


cmd_out = subprocess.run(['aliyun', 'ecs', 'DescribeRegions'], capture_output=True, text=True)
regions_list = json.loads(cmd_out.stdout)['Regions']['Region']
endpoint_map = {}
for r in regions_list:
    endpoint_map[r['RegionId']] = r['RegionEndpoint']

base_url = 'https://rhcos-redirector.apps.art.xq1c.p1.openshiftapps.com/art/storage/releases/rhcos-4.10/'

if len(sys.argv) > 1:
    base_url = sys.argv[1]

builds_url = base_url + 'builds.json'

builds_req = requests.get(builds_url)
builds = builds_req.json()['builds']

builds_list = []
[builds_list.append(b['id']) for b in builds if b['id'] not in builds_list]

failed_image_region = {}
for b in builds_list:
    meta_url = base_url + b + '/x86_64/meta.json'
    meta_req = requests.get(meta_url)
    meta = meta_req.json()

    if 'aliyun' not in meta:
        continue

    buildid = meta['buildid']
    image_desc = "OpenShift 4 " + buildid
    image_name = "rhcos-" + buildid

    aliyun = meta['aliyun']
    print(f'Modifying {buildid} with description "{image_desc}" and name {image_name}')
    for item in aliyun:
        region = item['name']
        image = item['id']
        endpoint = endpoint_map[region]
        base_cmd = ['aliyun', '--endpoint', endpoint, 'ecs']
        check_desc_cmd = base_cmd.copy() + ['DescribeImages', '--ImageId', image, '--RegionId', region]
        check_desc_out = subprocess.run(check_desc_cmd, capture_output=True, text=True)
        if check_desc_out.returncode != 0:
            failed_image_region[region] = image
            print(f"FAIL: Failed to get info about {image} in {region}")
            continue
        check_desc_json = json.loads(check_desc_out.stdout)
        if check_desc_json['TotalCount'] == 0:
            failed_image_region[region] = image
            print(f"FAIL: Image {image} not present in {region}")
            continue
        image_info = check_desc_json['Images']['Image'][0]
        if len(image_info['Description']) == 0 or len(image_info['ImageName']) == 0:
            modify_cmd = base_cmd.copy() + ['ModifyImageAttribute', '--ImageId', image, '--RegionId', region, '--Description', '"{}"'.format(image_desc), '--ImageName', image_name]
            modify_out = subprocess.run(modify_cmd, capture_output=True, text=True)
            if modify_out.returncode != 0:
                failed_image_region[region] = image
                print(f"FAIL: Failed to modify {image} in {region}")
                continue

    print(f"Finished modifying {buildid}")

if failed_image_region:
    print(failed_image_region.items())


