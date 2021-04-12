#!/usr/bin/env python

# TODO: Probably make a Class to share code
# TODO: Better error handling during copy/install operations
# TODO: Diff backup RPMs and currently installed RPMs

import argparse
import logging
import os
import re
import rpm
import shutil
import subprocess
import sys

BACKUP_DIR = ".local/share/toolbox-backup/"
YUM_REPOS_DIR = "/etc/yum.repos.d/"
CA_CERT_DIR = "/etc/pki/ca-trust/source/anchors/"

def backup(dir=None, repos=None, rpms=None, certs=None):
    if dir is None:
        dir = os.path.join(os.environ['HOME'], BACKUP_DIR)

    backup_dir_path=os.path.expanduser(dir)
    if not os.path.isdir(backup_dir_path):
        logging.debug(f"Making toolbox backup directory at {backup_dir_path}")
        os.mkdir(os.path.expanduser(backup_dir_path))

    # Backup everything by default; if one of the options is not None
    # then we'll only backup that part
    backup_all = True
    if repos or rpms or certs :
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


def restore(dir=None, repos=None, rpms=None, certs=None):
    if os.getuid() != 0:
        logging.error("Must run restore operation as superuser")
        sys.exit(1)

    if dir is None:
        dir = os.path.join("/var/home/", os.environ['SUDO_USER'], BACKUP_DIR)
    
    backup_dir_path=os.path.expanduser(dir)
    if not os.path.isdir(backup_dir_path):
        logging.error(f"Unable to find toolbox backup dir at {backup_dir_path}")
        sys.exit(1)

    restore_all = True
    if repos or rpms or certs:
        restore_all = False

    if restore_all or repos:
        yum_repo_backup_dir = os.path.join(backup_dir_path, "repos")
        if not os.path.isdir(yum_repo_backup_dir):
            logging.error(f"Unable to find repo backup dir at {yum_repo_backup_dir}")
            sys.exit(1)

        backup_repos = os.listdir(yum_repo_backup_dir)
        if len(backup_repos) < 1:
            logging.warning(f"Did not find any repo files in {yum_repo_backup_dir}")
        else:
            for repo in backup_repos:
                src = os.path.join(yum_repo_backup_dir, repo)
                dst = os.path.join(YUM_REPOS_DIR, repo)
                logging.debug(f"Restoring repo file {repo}")
                shutil.copy(src, dst)
        
    if restore_all or rpms:
        rpms_backup_file = os.path.join(backup_dir_path, "toolbox-rpms.backup")
        if not os.path.isfile(rpms_backup_file):
            logging.error(f"Unable to find RPM backup file at {rpms_backup_file}")
            sys.exit(1)
    
        with open(rpms_backup_file, 'r') as f:
            rpms = f.read()

        dnf_install = ['dnf', '-y', '--skip-broken', 'install']
        for r in rpms.split():
            dnf_install.append(r)
    
        logging.debug("Starting restore of RPMs")
        install_cp = subprocess.run(dnf_install, capture_output=True, text=True)
        if install_cp.returncode != 0:
            logging.error("Failed to restore RPMs from backup list")
            logging.error(install_cp.stderr)
            sys.exit(1)
    
        nomatch_re = re.compile("^No match for argument: (.*)")
        nomatch_rpms = []
        for l in install_cp.split("\n"):
            m = nomatch_re.match(l)
            if m:
                nomatch_rpms.append(m.group(1))
   
        if len(nomatch_rpms) > 0:
            logging.debug(f"Unable to install following RPMs: {nomatch_rpms}")
        
        logging.debug("Finished restoring RPMs")
        
    if restore_all or certs:
        cert_backup_dir = os.path.join(backup_dir_path, "certs")
        if not os.path.isdir(cert_backup_dir):
            logging.error(f"Unable to find the CA cert backup dir {cert_backup_dir}")
            sys.exit(1)
        
        backup_certs = os.listdir(cert_backup_dir)
        if len(backup_certs) < 1:
            logging.warning(f"Did not find any CA certs to restore at {cert_backup_dir}")
        else:
            for cert in backup_certs:
                src = os.path.join(cert_backup_dir, cert)
                dst = os.path.join(CA_CERT_DIR, cert)
                logging.debug(f"Restoring CA cert named {cert}")
                shutil.copy(src, dst)

            update_cp = subprocess.run(['update-ca-trust'], capture_output=True, text=True)
            if update_cp.returncode != 0:
                logging.error("Failed to update the CA trust")
                logging.error(update_cp.stderr)
                sys.exit(1)

            
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