#!/usr/bin/env python3

import argparse
import json
import requests
import sys

ARCHES = ['x86_64',
          'ppc64le',
          's390x']

BASEURI = 'https://releases-art-rhcos.svc.ci.openshift.org/art/storage/releases/'

RELEASES = ['rhcos-4.6', 
            'rhcos-4.5', 
            'rhcos-4.4', 
            'rchos-4.3',
            'rhcos-4.2',
            'rhcos-4.1']

class BuildInfo:
    BASEURI = 'https://releases-art-rhcos.svc.ci.openshift.org/art/storage/releases/'

    def __init__(self, release, arch, build):
        self.release = release
        self.arch = arch
        self.build = build

    def __make_release_arch_uri(self):
        self.release_arch_uri = None
        if self.arch != 'x86_64':
            self.release_arch_uri = BASEURI + self.release + '-' + self.arch
        else:
            self.release_arch_uri = BASEURI + self.release 
    
    def __make_base_build_uri(self):
        self.__make_release_arch_uri()
        self.base_build_uri = (self.release_arch_uri + '/' + 
                         self.build + '/' + self.arch)

    def __make_buildmeta_uri(self):
        self.__make_base_build_uri()
        self.meta_uri = self.base_build_uri + '/meta.json'

    def __make_commitmeta_uri(self):
        self.__make_base_build_uri()
        self.commitmeta_uri = self.base_build_uri + '/commitmeta.json'
    
    def show_release_arch_uri(self):
        self.__make_release_arch_uri()
        print(self.release_arch_uri)

    def show_packages(self):
        self.__make_commitmeta_uri()



    
    

def build_baseuri(release=None, arch=None):
    if release is None or arch is None:
        raise Exception('Must provide release and arch')
    
    if arch != 'x86_64':
        release_arch = release + '-' + arch 
    else:
        release_arch = release 
    
    return BASEURI + release_arch

def show_releases(arch=None):
    found_releases = []
    if arch is None:
        raise Exception('Must provide arch')
    
    for r in RELEASES:
        try:
            baseuri = build_baseuri(release=r, arch=arch)
        except:
            raise
        builds_url = baseuri + '/builds.json'
        req = requests.get(builds_url)
        if req.status_code == 200:
            found_releases.append(r)
   
    if found_releases:
        print(found_releases)
    else:
        raise Exception(f'ERROR: no valid releases found for {arch}')


def get_builds(release=None, arch=None, latest=10):
    ret_builds = []
    if arch is None or release is None:
        raise Exception('Must provide an arch and release')

    try:
        baseuri = build_baseuri(release=release, arch=arch)
    except:
        raise

    req = requests.get(baseuri + '/builds.json')
    if req.status_code != 200:
        raise Exception(f'Failed to successfully retrieve builds;' +
                        'status {req.status_code}')
    else:
        builds = req.json()
        for r in range(latest):
            ret_builds.append(builds['builds'][r]['id'])
    
    if ret_builds:
        print(ret_builds)
    else:
        raise Exception(f'No builds found for {release} on {arch}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('subcommand', 
                        help='Valid sub-commands: show-release get-builds buildinfo')
    parser.add_argument('--arch', default='x86_64', 
                        help='Architecture; defaults to x86_64')
    parser.add_argument('--release', default=RELEASES[0], 
                        help=f'RHCOS release; defaults to {RELEASES[0]}')
    parser.add_argument('--build', default=None, help='Build ID')
    args = parser.parse_args()

    if args.arch not in ARCHES:
        print(f'ERROR: {args.arch} is not a supported arch')
        sys.exit(1)   

    if args.release not in RELEASES:
        print(f'ERROR: {args.release} is not a valid release')
        sys.exit(1)

    if args.subcommand == 'show-releases':
        try:
            show_releases(arch=args.arch)
        except Exception as e:
            print(e)
            sys.exit(1)
    elif args.subcommand == 'get-builds':
        try:
            get_builds(release=args.release, arch=args.arch)
        except Exception as e:
            print(e)
            sys.exit(1)
    elif args.subcommand == 'buildinfo':
        if args.build is None:
            print(f'ERROR: must supply valid build ID')
            sys.exit(1)

        build_info = BuildInfo(release=args.release, arch=args.build, build=args.build)
        build_info.show_release_arch_uri()
    else:
        print(f'ERROR: valid subcommand required')
        sys.exit(1)


if __name__ == "__main__":
    main()
