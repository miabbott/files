#!/usr/bin/env python3

import argparse
from collections import OrderedDict
import datetime
import requests
import sys

BASEURL = 'https://releases-art-rhcos.svc.ci.openshift.org/art/storage/releases/'
RELEASES = ['rhcos-4.4',
            'rhcos-4.4-ppc64le',
            'rhcos-4.4-s390x',
            'rhcos-4.5',
            'rhcos-4.5-ppc64le',
            'rhcos-4.5-s390x',
            'rhcos-4.6',
            'rhcos-4.6-ppc64le',
            'rhcos-4.6-s390x',
            'rhcos-4.7',
            'rhcos-4.7-ppc64le',
            'rhcos-4.7-s390x',
            'rhcos-4.8',
            'rhcos-4.8-ppc64le',
            'rhcos-4.8-s390x']


def get_builds(release):
    build_list = []
    builds_url = BASEURL + release + '/builds.json'
    builds_req = requests.get(builds_url)
    if builds_req.status_code != 200:
        raise Exception('Failed to retrieve list of builds')
    for bld in builds_req.json()['builds']:
        build_list.append(bld['id'])

    return build_list

def find_package(package=None, release=None):
    if package is None:
        raise Exception('Must provide package name')
    if release is None:
        raise Exception('Must provide release')

    arch = 'x86_64'
    split_release = release.split('-')
    if len(split_release) > 2:
        arch = split_release[2]

    try:
        release_builds = get_builds(release)
    except:
        raise

    build_package_map = OrderedDict()
    for bld in release_builds:
        cm_url = f'{BASEURL}/{release}/{bld}/{arch}/commitmeta.json'
        #print(f'url = {cm_url}')
        cm_req = requests.get(cm_url)
        if cm_req.status_code != 200:
            raise Exception(f'Failed to retrieve commitmeta for {bld}: status code = {cm_req.status_code}')
        rpmdb = cm_req.json()['rpmostree.rpmdb.pkglist']
        for rpm in rpmdb:
            nvr = f'{rpm[0]}-{rpm[2]}-{rpm[3]}.{rpm[4]}'
            if rpm[0] == package and nvr not in build_package_map.values():
                build_package_map[bld] = nvr
                break

    return build_package_map

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--release', action="store", help='Release to search',
                        choices=RELEASES)
    parser.add_argument('--package', action="store", help='Package to query')
    args = parser.parse_args()

    try:
        bmp = find_package(package=args.package, release=args.release)
    except Exception as err:
        print(err)
        sys.exit(1)
    if bmp:
        while bmp:
            build, rpm = bmp.popitem()
            build_s = build.split('.')
            date = build_s[2].split('-')[0]
            date_time_obj = datetime.datetime.strptime(date, '%Y%m%d%H%M')
            print(f'{build} = {rpm} on {date_time_obj}')
    else:
        print(f'Unable to find {args.package} in any builds')
        sys.exit(1)


if __name__ == "__main__":
    main()
