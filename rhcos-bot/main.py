#!/usr/bin/env python3

# TODO: figure out best way to represent releases as a class?
# TODO: docstrings
# TODD: proper Exceptions in BuildInfo class

import argparse
import sys

import requests

ARCHES = ['x86_64',
          'ppc64le',
          's390x']

BASEURI = 'https://releases-art-rhcos.svc.ci.openshift.org/art/storage/releases/' # noqa

RELEASES = ['rhcos-4.6',
            'rhcos-4.5',
            'rhcos-4.4',
            'rchos-4.3',
            'rhcos-4.2',
            'rhcos-4.1']


class BuildInfo:
    BASEURI = 'https://releases-art-rhcos.svc.ci.openshift.org/art/storage/releases/' # noqa

    def __init__(self, release, arch, build):
        if release not in RELEASES:
            raise Exception(f'Not a valid release: {release}')

        if arch not in ARCHES:
            raise Exception(f'Not a valid architecture: {arch}')

        self.release = release
        self.arch = arch
        self.build = build
        self.commitmeta_json = {}
        self.packages = []
        self.rpmdb = {}

        # need to build different subdir for multi-arch
        if self.arch != 'x86_64':
            release_arch_uri = BASEURI + self.release + '-' + self.arch
        else:
            release_arch_uri = BASEURI + self.release

        # ex:  https://releases-art-rhcos.svc.ci.openshift.org/art/storage/releases/rhcos-4.6-ppc64le/46.82.202010082145-0/ppc64le/ # noqa
        self.base_build_uri = (release_arch_uri + '/' +
                               self.build + '/' + self.arch + '/')


    def _get_commitmeta_json(self):
        commitmeta_uri = self.base_build_uri + 'commitmeta.json'
        commitmeta_req = requests.get(commitmeta_uri)
        if commitmeta_req.status_code != 200:
            print(f'ERROR: failed to retrieve {commitmeta_uri}')
            raise Exception('Unable to get commitmeta JSON for build ' +
                            f'{self.build}: status {commitmeta_req.status_code}')

        self.commitmeta_json = commitmeta_req.json()

    def _get_all_packages(self):
        self._get_commitmeta_json()
        self.rpmdb = self.commitmeta_json['rpmostree.rpmdb.pkglist']
        for pkg in self.rpmdb:
            self.packages.append(pkg[0])

        if not self.packages:
            raise Exception(f'No packages found for build {self.build}')

    def show_all_packages(self):
        self._get_all_packages()
        print(self.packages)

    def get_package_version(self, package=None):
        if package is None:
            raise Exception('Must provide a package name')

        self._get_all_packages()
        if package not in self.packages:
            raise Exception(f'Unable to find {package} in build')

        for pkg in self.rpmdb:
            if package == pkg[0]:
                name = pkg[0]
                ver = pkg[2]
                rel = pkg[3]
                arch = pkg[4]
                break

        print(f'{name}-{ver}-{rel}.{arch}')



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

    for rel in RELEASES:
        baseuri = build_baseuri(release=rel, arch=arch)
        builds_url = baseuri + '/builds.json'
        req = requests.get(builds_url)
        if req.status_code == 200:
            if arch != 'x86_64':
                found_releases.append(rel + '-' + arch)
            else:
                found_releases.append(rel)

    if found_releases:
        print(found_releases)
    else:
        raise Exception(f'ERROR: no valid releases found for {arch}')


def get_builds(release=None, arch=None, latest=None):
    ret_builds = []
    if arch is None or release is None:
        raise Exception('Must provide an arch and release')

    if latest is None:
        raise Exception('Must provide value for latest')

    baseuri = build_baseuri(release=release, arch=arch)

    req = requests.get(baseuri + '/builds.json')
    if req.status_code != 200:
        raise Exception('Failed to successfully retrieve builds;' +
                        f'status {req.status_code}')

    builds = req.json()
    if latest != 'all':
        for bld in range(int(latest)):
            ret_builds.append(builds['builds'][bld]['id'])
    else:
        for bld in builds['builds']:
            ret_builds.append(bld['id'])

    if ret_builds:
        print(ret_builds)
    else:
        raise Exception(f'No builds found for {release} on {arch}')


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
            show_releases(arch=args.arch)
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
            get_builds(release=args.release, arch=args.arch,
                       latest=args.latest)
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
