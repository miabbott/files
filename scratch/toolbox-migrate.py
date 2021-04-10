#!/usr/bin/env python

import argparse
import logging
import os
import re
import rpm
import shutil

BACKUP_DIR = "~/.local/share/toolbox-backup/"
YUM_REPOS_DIR = "/etc/yum.repos.d/"
CA_CERT_DIR = "/etc/pki/ca-trust/source/anchors/"

def backup(dir=None, repos=None, rpms=None, certs=None):
    if dir is None:
        dir = BACKUP_DIR
    
    backup_dir_path=os.path.expanduser(dir)
    if not os.path.isdir(backup_dir_path):
        logging.debug(f"Making toolbox backup directory at {backup_dir_path}")
        os.mkdir(os.path.expanduser(backup_dir_path))

    # Backup everything by default; if one of the options is not None
    # then we'll only backup that part
    backup_all = True
    if repos is not None or rpms is not None or certs is not None:
        backup_all = False

    if backup_all or repos:
        fedora_re = re.compile('^fedora.*')
        yum_repos_dir = os.listdir(YUM_REPOS_DIR)
        yum_repo_backup_dir = os.path.join(backup_dir_path, "repos")
        if not os.path.isdir(yum_repo_backup_dir):
            logging.debug(f"Making yum repo backup dir at {yum_repo_backup_dir}")
            os.mkdir(yum_repo_backup_dir)

        for repo in yum_repos_dir:
            fedora_match = fedora_re.match(repo)
            if not fedora_match:
                src = os.path.join(YUM_REPOS_DIR, repo)
                dst = os.path.join(yum_repo_backup_dir, repo)
                logging.debug(f"Backing up yum repo file {repo}")
                shutil.copy(src, dst)

    if backup_all or rpms:
        rpm_backup = os.path.join(backup_dir_path, "toolbox-rpms.backup")
        logging.debug(f"Backing up names of installed RPMs to {rpm_backup}")
        txn_set = rpm.TransactionSet()
        rpmdb = txn_set.dbMatch()
        with open(rpm_backup, 'w') as f:
            for rpms in rpmdb:
                f.write(f"{rpms['name']} ")

    if backup_all or certs:
        cert_list = os.listdir(CA_CERT_DIR)
        cert_backup_dir = os.path.join(backup_dir_path, "certs")
        if not os.path.isdir(cert_backup_dir):
            logging.debug(f"Making CA cert backup dir at {cert_backup_dir}")
            os.mkdir(cert_backup_dir)

        for cert in cert_list:
            src = os.path.join(CA_CERT_DIR, cert)
            dst = os.path.join(cert_backup_dir, cert)
            logging.debug(f"Backing up CA cert {cert}")
            shutil.copy(src, dst)            

    logging.debug("Backup of toolbox config complete")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('operation',
        choices=['backup','cleanup','restore'], 
        help="The operation to perform")
    parser.add_argument('--verbose', action='store_true',
        help="Make the operation more talkative")
    parser.add_argument('--dir', 
        help="Specify custom directory location to use for operations")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--repos', action='store_true', 
        help="Only operate on yum repos")
    group.add_argument('--rpms', action='store_true',   
        help="Only operate on installed RPMs")
    group.add_argument('--certs', action='store_true',
        help="Only operate on installed CA certs")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    if args.operation == "backup":
        backup(dir=args.dir, repos=args.repos, 
            rpms=args.rpms, certs=args.certs)

    if args.operation == "restore":
        restore(dir=args.dir, repos=args.repos, 
            rpms=args.rpms, certs=args.certs)

    if args.operation == "cleanup":
        cleanup(dir=args.dir, repos=args.repos, 
            rpms=args.rpms, certs=args.certs)

if __name__ == "__main__":
    main()