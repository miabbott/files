#!/usr/bin/env python3

import argparse
import subprocess
import sys
import shutil
import tempfile

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo-file', help="file name containing a list of git repos")
    parser.add_argument('--author-file', help="file name containing a list of author emails")
    args = parser.parse_args()

    with open(args.repo_file, 'r') as rf:
        repo_list = rf.readlines()

    with open(args.author_file, 'r') as af:
        author_list = af.read().splitlines()

    git_clone=['git', 'clone', '-n']
    git_log=['log', '--pretty=format:%ae', '--since', 'Jan 1 2021', '--until', 'Dec 31 2021']

    commit_count = 0
    for repo in repo_list:
        dirpath = tempfile.mkdtemp()
        clone_tmp = git_clone.copy()
        clone_tmp.extend([repo.strip(), dirpath])
        subprocess.run(clone_tmp)
        git_dirpath = dirpath + '/.git'
        log_cmd = ['git', '--git-dir', git_dirpath]
        log_cmd.extend(git_log)
        print(log_cmd)
        log_out = subprocess.run(log_cmd, capture_output=True, text=True)
        for l in log_out.stdout.split('\n'):
            if l in author_list:
                commit_count += 1
        shutil.rmtree(dirpath)

    print(commit_count)

if __name__ == "__main__":
    main()
