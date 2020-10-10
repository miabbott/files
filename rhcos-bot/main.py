#!/usr/bin/env python3

import argparse
import requests
import sys

ARCHES = ['x86_64',
          'ppc64le',
          's390x']

BASEURI = 'https://releases-art-rhcos.svc.ci.openshift.org/art/storage/releases/'

RELEASES = ['rhcos-4.1', 
            'rhcos-4.2', 
            'rhcos-4.3', 
            'rchos-4.4',
            'rhcos-4.5',
            'rhcos-4.6']

def build_baseuri(arch='x86_64'):
    if arch != 'x86_64':
        release = r + '-' + arch 
    else:
        release = r 
    return BASEURI + release

def show_releases(arch='x86_64'):
    found_releases = []
    for r in RELEASES:
        baseuri = build_baseuri(arch)
        builds_url = baseuri + '/builds.json'
        #print(f'DEBUG: {builds_url}')
        req = requests.get(builds_url)
        #print(f'DEBUG: {req.status_code}')
        if req.status_code == 200:
            found_releases.append(release)
    #print(f'DEBUG: {found_releases}')        
    if found_releases:
        print(found_releases)
    else:
        print(f'ERROR: no valid releases found for {arch}')


def is_valid_release(release):
    return release in RELEASES


def get_builds(arch='x86_64', latest='10'):
    baseuri = build_baseuri(arch)
    req = requests.get(


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('subcommand')
    parser.add_argument('--arch', default='x86_64')
    args = parser.parse_args()

    if args.arch not in ARCHES:
        print(f'ERROR: {args.arch} is not a supported arch')
        sys.exit(1)   

    if args.subcommand == "show-releases":
        show_releases(arch=args.arch)


if __name__ == "__main__":
    main()
