#!/usr/bin/env python3

# Scractch script to share Aliyun replicated images with accounts

import json
import re
import requests
import subprocess
import sys

# see https://issues.redhat.com/browse/SPLAT-193 for account values
CI = "5920522175273455"
ALI = "1474626365013525"
DEV = "5807403157081522"
QE = "5724326381648897"

# use any available meta.json URL for this. removed since it pointed to internal URL.
url = 'https://rhcos-redirector.apps.art.xq1c.p1.openshiftapps.com/art/storage/releases/rhcos-4.10/410.84.202112040202-0/x86_64/meta.json'
req = requests.get(url)
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
    cmd = ['aliyun', '--endpoint', endpoint, '--profile', 'art-rhcos-upload-amis', 'ecs', 'ModifyImageSharePermission']
    cmd.extend(['--ImageId', id])
    cmd.extend(['--RegionId', region])
    cmd.extend(['--AddAccount.1', CI])
    cmd.extend(['--AddAccount.2', DEV])
    cmd.extend(['--AddAccount.3', QE])
    print(f'Sharing image {id} in {region}')
    print(' '.join(cmd))
    command = subprocess.run(cmd, capture_output=True, text=True)
    if command.returncode != 0:
        print("Failed to share image")    # frustratingly the `aliyun` CLI returns error messages to stdout
        print(command.stdout)
        print(command.stderr)

    # remove the AddAccount args
    del cmd[11:]
    cmd.extend(['--IsPublic', 'true'])
    print(f'Making {id} public in region {region}')
    print(' '.join(cmd))
    command = subprocess.run(cmd, capture_output=True, text=True)
    if command.returncode != 0:
        print("Failed to make image public")    # frustratingly the `aliyun` CLI returns error messages to stdout
        print(command.stdout)
        print(command.stderr)