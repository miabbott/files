#!/usr/bin/env python3

# Scractch script to share Aliyun replicated images with accounts

import requests
import subprocess
import sys

# see https://issues.redhat.com/browse/SPLAT-193 for account values
CI = "XXX"
ALI = "XXX"

# use any available meta.json URL for this. removed since it pointed to internal URL.
req = requests.get('XXX')
meta = req.json()

aliyun = meta['aliyun']

for image in aliyun:
    region = image['name']
    id = image['id']
    # For *some* regions in Aliyun you have to use a specific endpoint, which is madness
    endpoint = f'ecs.{region}.aliyuncs.com'
    if region in ['us-east-1', 'us-west-1', 'cn-qingdao', 'cn-beijing', 'cn-hangzhou', 'cn-shanghai', 'cn-shanghai', 'cn-hongkong', 'ap-southeast-1']:
        endpoint = 'ecs.aliyuncs.com'
    # aliyun --profile rhcos-upload-amis ecs ModifyImageSharePermission --ImageId XXX --RegionId XXX --AddAccount.1 XXX
    cmd = ['aliyun', '--endpoint', endpoint, '--profile', 'rhcos-upload-amis', 'ecs', 'ModifyImageSharePermission']
    cmd.append('--ImageId')
    cmd.append(id)
    cmd.append('--RegionId')
    cmd.append(region)
    cmd.append('--AddAccount.1')
    cmd.append(CI)
    cmd.append('--AddAccount.2')
    cmd.append(ALI)
    print(f'Sharing image {id} in {region}')
    command = subprocess.run(cmd, capture_output=True, text=True)
    if command.returncode != 0:
        print("Failed to share image")
        print(cmd)
        # frustratingly the `aliyun` CLI returns error messages to stdout
        print(command.stdout)
        print(command.stderr)
        sys.exit(1)
