#!/usr/bin/env python3

'''
A utility program to dump out when a package changed during the lifetime of
an OCP release.

Example usage & output:

$ ./pkg_report.py --release rhcos-4.7 --package shim-x64
47.82.202010110827-0 = shim-x64-15-15.el8_2.x86_64 on 2020-10-11 08:27:00
47.82.202011041142-0 = shim-x64-15-16.el8.x86_64 on 2020-11-04 11:42:00

TODO: store data in sqlite database to speed up execution
'''

import argparse
from collections import OrderedDict
import datetime
import requests
import sys

BASEURL = 'https://rhcos-redirector.ci.openshift.org/art/storage/releases/'
RELEASES = ['rhcos-4.3',
            'rhcos-4.4',
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
    '''
    Given a release version string, return a sorted list of build numbers
    '''
    build_list = []
    builds_url = BASEURL + release + '/builds.json'
    builds_req = requests.get(builds_url)
    if builds_req.status_code != 200:
        raise Exception('Failed to retrieve list of builds')
    for bld in builds_req.json()['builds']:
        build_list.append(bld['id'])

    build_list.sort()
    return build_list


def map_rpm_to_versions(package=None, release=None):
    '''
    Given a package/RPM name and a OCP release version string, produce
    an OrderedDict of "version = {previous_version, nvr}" entries
    '''
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
    except Exception as err:
        raise err

    # we want to preserve the order of the builds, so use an OrderedDict
    build_package_map = OrderedDict()
    # we need the length of the sorted list of builds, so we can easily
    # index the current build and previous build
    release_builds_len = len(release_builds)
    for bld in range(release_builds_len):
        current_ver = release_builds[bld]

        if bld == 0:
            previous_ver = None
        else:
            previous_ver = release_builds[bld - 1]

        current_cm_url = (f'{BASEURL}/{release}/{current_ver}/'
                          f'{arch}/commitmeta.json')
        current_cm_req = requests.get(current_cm_url)
        if current_cm_req.status_code != 200:
            raise Exception('Failed to retrieve commitmeta for '
                            f'{current_ver}: status code = '
                            f'{current_cm_req.status_code}')

        rpmdb = current_cm_req.json()['rpmostree.rpmdb.pkglist']
        for rpm in rpmdb:
            nvr = f'{rpm[0]}-{rpm[2]}-{rpm[3]}.{rpm[4]}'
            if rpm[0] == package:
                build_package_map[current_ver] = (previous_ver, nvr)
                break

    return build_package_map


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--release', action='store', help='Release to search',
                        choices=RELEASES)
    parser.add_argument('--package', action='store', help='Package to query')
    args = parser.parse_args()

    try:
        build_package_map = map_rpm_to_versions(package=args.package,
                                                release=args.release)
    except Exception as err:
        print('Received an Exception while doing the RPM to version'
              f'mapping: {err}')
        sys.exit(1)

    # once we have mapping, we want to print a line each time the NVR of the
    # package changed.
    if build_package_map:
        for ver in build_package_map.keys():
            prev_ver, rpm = build_package_map[ver]
            if prev_ver is not None:
                pv, pr = build_package_map[prev_ver]
                if rpm == pr:
                    continue
            ver_s = ver.split('.')
            date = ver_s[2].split('-')[0]
            date_time_obj = datetime.datetime.strptime(date, '%Y%m%d%H%M')
            print(f'{ver} = {rpm} on {date_time_obj}')
    else:
        print(f'Unable to find {args.package} in any builds')
        sys.exit(1)


if __name__ == '__main__':
    main()
