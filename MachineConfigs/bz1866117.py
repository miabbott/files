#!/usr/bin/env python

import base64
import random
import string
import yaml

def b64string(instring):
    b64b_string = base64.b64encode(instring.encode('ascii'))
    return b64b_string.decode('ascii')

def main():
    infile = "bz1866117-stub.yaml"
    outfile = "bz1866117-out.yaml"
    rootdir = "/var/srv/"
    sourceb = "data:text/plain;charset=utf-8;base64,"

    files = []
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits

    for _ in range(0, 100):
        # generate random filename under rootdir
        filepath = rootdir + ''.join(random.choices(chars, k=12))
        # generate random file contents that are b64 encoded
        rand_chars = ''.join(random.choices(chars, k=100))
        full_source = sourceb + b64string(rand_chars)
        # build the dict for the file entry and add to files list
        filedef = {'contents': {'source': full_source}, 'filesystem': 'root', 'path': filepath}
        files.append(filedef)

    with open(infile) as fin:
        data = yaml.load(fin, Loader=yaml.FullLoader)
        data['spec']['config']['storage']['files'] = files

    with open(outfile, 'w') as fout:
        yaml.dump(data, fout)

if __name__ == "__main__":
    main()
