#!/usr/bin/env python3

# TODO: figure out best way to represent releases as a class?
# TODO: docstrings
# TODD: proper Exceptions in BuildInfo class

import argparse
import sys

import requests

from buildinfo import BuildInfo
from releases import Releases, ReleaseInfo


# def show_releases(arch=None):
#     found_releases = []
#     if arch is None:
#         raise Exception('Must provide arch')

#     for rel in RELEASES:
#         baseuri = build_baseuri(release=rel, arch=arch)
#         builds_url = baseuri + '/builds.json'
#         req = requests.get(builds_url)
#         if req.status_code == 200:
#             if arch != 'x86_64':
#                 found_releases.append(rel + '-' + arch)
#             else:
#                 found_releases.append(rel)

#     if found_releases:
#         print(found_releases)
#     else:
#         raise Exception(f'ERROR: no valid releases found for {arch}')


# def get_builds(release=None, arch=None, latest=None):
#     ret_builds = []
#     if arch is None or release is None:
#         raise Exception('Must provide an arch and release')

#     if latest is None:
#         raise Exception('Must provide value for latest')

#     baseuri = build_baseuri(release=release, arch=arch)

#     req = requests.get(baseuri + '/builds.json')
#     if req.status_code != 200:
#         raise Exception('Failed to successfully retrieve builds;' +
#                         f'status {req.status_code}')

#     builds = req.json()
#     if latest != 'all':
#         for bld in range(int(latest)):
#             ret_builds.append(builds['builds'][bld]['id'])
#     else:
#         for bld in builds['builds']:
#             ret_builds.append(bld['id'])

#     if ret_builds:
#         print(ret_builds)
#     else:
#         raise Exception(f'No builds found for {release} on {arch}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--arch', default='x86_64',
                        help='Architecture; defaults to x86_64')
    subparsers = parser.add_subparsers(dest='action')
    parser_show_releases = subparsers.add_parser('show-releases')
    parser_get_builds = subparsers.add_parser('get-builds')
    parser_get_builds.add_argument('--release', default=RELEASES[0],
                                   help='RHCOS release; defaults to ' +
                                   f'{RELEASES[0]}')
    parser_get_builds.add_argument('--latest', metavar='N', default=10,
                                   help='Retrieve latest N build IDs; ' +
                                        'default 10')
    parser_get_builds.add_argument('--all', action='store_true',
                                   help='Show all builds')
    parser_show_packages = subparsers.add_parser('show-packages')
    parser_show_packages.add_argument('--build', default=None,
                                   help='Build ID')
    parser_show_packages.add_argument('--release', default=RELEASES[0],
                                   help='RHCOS release; defaults to ' +
                                   f'{RELEASES[0]}')
    parser_get_package = subparsers.add_parser('get-package')
    parser_get_package.add_argument('--package', default=None,
                                    help='Package name')
    parser_get_package.add_argument('--build', default=None,
                                    help='Build ID')
    parser_get_package.add_argument('--release', default=RELEASES[0],
                                   help='RHCOS release; defaults to ' +
                                   f'{RELEASES[0]}')
    args = parser.parse_args()

    if args.arch not in ARCHES:
        print(f'ERROR: {args.arch} is not a supported arch')
        sys.exit(1)

    if args.action == 'show-releases':
        try:
            releases = Releases(arch=args.arch)
            print(releases.show_releases())
        except Exception as exc:
            print(exc)
            sys.exit(1)
    elif args.action == 'get-builds':
        if args.release not in RELEASES:
            print(f'ERROR: {args.release} is not a valid release')
            sys.exit(1)

        if args.all:
            args.latest = 'all'
        try:
            release = ReleaseInfo(release=args.release, arch=args.arch)
            print(release.get_builds(number=args.latest))
        except Exception as exc:
            print(exc)
            sys.exit(1)
    elif args.action == 'show-packages':
        if args.build is None:
            print('ERROR: must supply valid build ID')
            sys.exit(1)
        try:
            build_info = BuildInfo(release=args.release,
                                   arch=args.arch, build=args.build)
            build_info.show_all_packages()
        except Exception as exc:
            print(exc)
            sys.exit(1)
    elif args.action == 'get-package':
        if args.package is None or args.build is None:
            print('ERROR: must supply package name and build ID')
            sys.exit(1)
        try:
            build_info = BuildInfo(release=args.release,
                                   arch=args.arch, build=args.build)
            build_info.get_package_version(package=args.package)
        except Exception as exc:
            print(exc)
            sys.exit(1)
    else:
        print('ERROR: valid subcommand required')
        sys.exit(1)


if __name__ == "__main__":
    main()
