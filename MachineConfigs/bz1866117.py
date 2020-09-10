#!/usr/bin/env python

import yaml

infile = "bz1866117-stub.yaml"
outfile = "bz1866117-out.yaml"
rootdir = "/var/srv"
source = "data:text/plain;charset=utf-8;base64,aGVsbG8gd29ybGQK"

files = []
for i in range(0,100):
    filepath = rootdir + 'hello-world' + str(i) + '.txt'
    e = {'contents': {'source': source}, 'filesystem': 'root', 'path': filepath}
    files.append(e)

with open(infile) as fin:
    data = yaml.load(fin, Loader=yaml.FullLoader)
    data['spec']['config']['storage']['files'] = files

with open(outfile, 'w') as fout:
    d = yaml.dump(data, fout)
