#!/usr/bin/python

# Utility script to confirm if the latest machine-os-content images pushed to
# Quay are using the v2s2 format

import json
import logging
import subprocess

import requests

V2S2 = "application/vnd.docker.distribution.manifest.v2+json"

BASEURL = "https://rhcos-redirector.apps.art.xq1c.p1.openshiftapps.com/art/storage/releases"

def get_latest_build(release, arch):
    full_rel = "rhcos-{}-{}".format(release, arch)
    if arch == "x86_64":
        full_rel = "rhcos-{}".format(release)

    builds_url = "{}/{}/builds.json".format(BASEURL, full_rel)

    builds_resp = requests.get(builds_url)
    if builds_resp.status_code == 403:
        logging.error("No builds for %s on arch %s", release, arch)
        return None

    builds_json = builds_resp.json()

    latest_build = builds_json['builds'][0]['id']

    return latest_build

def get_moc(release, arch, build):
    full_rel = "rhcos-{}-{}".format(release, arch)
    if arch == "x86_64":
        full_rel = "rhcos-{}".format(release)

    build_url = "{}/{}/{}/{}/meta.json".format(BASEURL, full_rel, build, arch)

    build_resp = requests.get(build_url)
    meta_json = build_resp.json()

    moc = "{}@{}".format(meta_json['oscontainer']['image'], meta_json['oscontainer']['digest'])

    return moc

def get_image_format(moc):
    cmd = ["oc", "image", "info", "-o", "json", moc]

    cmd_out = subprocess.run(cmd, capture_output=True, text=True,
                             encoding="utf-8", check=False)

    info_json = json.loads(cmd_out.stdout)
    img_format = info_json['mediaType']

    return img_format


def main():
    arches = ["aarch64", "ppc64le", "s390x", "x86_64"]
    releases = ["4.6", "4.7", "4.8", "4.9", "4.10", "4.11"]

    allclear = True

    logging.basicConfig(level=logging.WARNING)

    for release in releases:
        for arch in arches:
            if release in ["4.6", "4.7"] and arch == "aarch64":
                logging.warning("Skipping aarch64 on %s", release)
                break

            latest_build = get_latest_build(release, arch)
            if latest_build is None:
                # if there is no latest build, we haven't fixed everything
                allclear = False
                continue

            moc = get_moc(release, arch, latest_build)
            logging.info("Checking %s for arch %s", latest_build, arch)
            img_fmt = get_image_format(moc)

            if img_fmt != V2S2:
                msg = ("Latest build %s for %s on arch %s " %
                       (latest_build, release, arch) + "is not v2s2 format!")
                logging.error(msg)
                allclear = False
            else:
                msg = ("Latest build %s for %s on arch %s " %
                       (latest_build, release, arch) + "is v2s2 format!")
                logging.info(msg)

    if allclear:
        print("All of the latest machine-os-content images are using v2s2!")

if __name__ == "__main__":
    main()
