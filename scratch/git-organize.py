#!/usr/bin/python3

# Utility script to migrate existing git repos on disk to a more
# organized hierarchy based on domain name and sub directories

import argparse
import logging
import os
import subprocess
import sys
from shutil import copytree
from pathlib import Path


# helper function to run commands and return a list of strings
def run_command(cmd):
    sp = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    return [l.decode("utf-8").rstrip("\n") for l in sp.stdout]


# takes a git remote URL and returns a string that looks like a path
# using the domain name and the subdirs
# i.e. https://github.com/coreos/ignition.git -> github.com/coreos/ignition
def process_url(url):
    new_dir = None
    split_url = url.removesuffix(".git").split("/")

    # e.g. https://github.com/coreos/ignition.git
    # split_url == ['https:', '', 'github.com', 'coreos', 'ignition']
    # e.g  git://github.com:443/coreos/ignition.git
    # split_url == ['git:', '', 'github.com:443', 'coreos', 'ignition']
    if split_url[0].startswith('http') or split_url[0].startswith('git:'):
        # trim off any port specification from domain name
        tmp_list = [split_url[2].split(":")[0]]
        for i in split_url[3::]:
            tmp_list.append(i)
        new_dir = "/".join(tmp_list)

    # e.g. git@github.com:coreos/ignition.git
    # split_url == ['git@github.com:coreos', 'ignition']
    if split_url[0].startswith('git@'):
        tmp_list = split_url[0].removeprefix("git@").split(":")
        tmp_list.append(split_url[1])
        new_dir = "/".join(tmp_list)

    # e.g. ssh://user@github.com:22coreos/ignition.git
    # e.g. ssh://github.com/coreos/ignition.git
    # split_url == ['ssh:', '', 'user@github.com:22', 'coreos', 'ignition']
    if split_url[0].startswith('ssh:'):
        # trim off any port specification from domain name portion
        domain = split_url[2].split(":")[0]
        if "@" in domain:
            tmp_list = [domain.split("@")[1]]
        else:
            tmp_list = [domain]

        for i in split_url[3::]:
            tmp_list.append(i)

        new_dir = "/".join(tmp_list)

    return new_dir


# iterates through a directory to find all git repos and tries to organize them sanely
# according to domain name and subdirectories
def main():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)

    parser = argparse.ArgumentParser()
    parser.add_argument('dir', help="starting directory", default=os.curdir)
    parser.add_argument("-d", "--debug", help="Debug logging", action="store_true")
    args = parser.parse_args()


    if args.debug:
        logger.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)

    starting_dir = args.dir

    # shell out to find command to locate all .git dirs
    dirs = run_command(['find', starting_dir, '-type', 'd', '-name', '*.git'])

    # holding vars to report any troubles later
    baddirs = []
    weird_remotes = {}

    for d in dirs:
        (headdir, _) = os.path.split(d)
        os.chdir(headdir)
        remotes = run_command(['git', 'remote'])
        for r in remotes:
            # prefer the upstream remote
            if r == "upstream":
                remote = r
                break

            if r == "origin":
                remote = r
            else:
                remote = None

        if remote is None:
            baddirs.append(headdir)
            logger.debug("Could not find suitable remote for %s", headdir)
            continue

        url = run_command(['git', 'remote', 'get-url', remote])

        new_dir = process_url(url[0])

        # make a new directory and move the existing content over
        if new_dir is not None:
            new_path = os.path.join(starting_dir, new_dir)
            # use a marker file to avoid copying existing data
            marker_file = os.path.join(new_path, ".git-organize-complete")
            os.makedirs(new_path, exist_ok=True)
            if not os.path.isfile(marker_file):
                copytree(headdir, new_path, symlinks=True, dirs_exist_ok=True)
                Path(marker_file).touch()
                logger.debug("Migrated %s to %s", headdir, new_path)
            else:
                logger.debug("Already migrated %s to %s", headdir, new_path)
        else:
            logger.debug("Found weird remote URL for %s", headdir)
            weird_remotes[headdir] = url[0]

    if len(baddirs) != 0:
        logger.error("Need to take manual action on the following " +
                     "directories due to non-standard remote name: ")
        for bd in baddirs:
            print(f'\t{bd}')

    if len(weird_remotes) != 0:
        logger.error("Need to take additional action on the following " +
                     "directories due to weird remote URLs: ")
        for k,v in weird_remotes.items():
            print(f'\t{k} {v}')


if __name__ == '__main__':
    sys.exit(main())
