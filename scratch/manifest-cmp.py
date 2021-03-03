#!/usr/bin/env python3

import argparse
import os
import sys
import yaml


def build_pkg_list(manifest):
    dir = os.path.dirname(manifest)
    full_pkg_list = []
    with open(manifest, 'r') as mani:
        try:
            all_yaml = yaml.safe_load(mani)
        except yaml.YAMLError as exc:
            raise exc
    
    if "include" in all_yaml.keys():
        includes = all_yaml["include"]
        if type(includes) is not list:
            includes = [all_yaml["include"]]
        for inc in includes:
            fp_inc = os.path.join(dir, inc)
            inc_pkg_list = build_pkg_list(fp_inc)
            full_pkg_list += inc_pkg_list

    if "packages" in all_yaml.keys():
        pkgs = all_yaml["packages"]
        for entry in pkgs:
            if "'" in entry:
                entry_list = [pkg for pkg in entry.split("'") if len(pkg) > 1]
            else:
                entry_list = entry.split()
            for el in entry_list:
                full_pkg_list.append(el)
    
    return full_pkg_list

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fcos", "-f", help="fcos manifest", required=True)
    parser.add_argument("--rhcos", "-r", help="rhcos manifest", required=True)
    args = parser.parse_args()

    if not os.path.exists(args.fcos):
        sys.exit("FCOS manifest does not exist")

    if not os.path.exists(args.rhcos):
        sys.exit("RHCOS manifest does not exist")

    fcos_pkgs = build_pkg_list(args.fcos)
    rhcos_pkgs = build_pkg_list(args.rhcos)

    fcos_pkgs.sort()
    rhcos_pkgs.sort()

    same_pkgs = [pkg for pkg in fcos_pkgs if pkg in rhcos_pkgs]
    print(same_pkgs)
    # print(fcos_pkgs)
    # print(rhcos_pkgs)

if __name__ == "__main__":
    main()
