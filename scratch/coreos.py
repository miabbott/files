#!/usr/bin/env python3

from datetime import datetime
from github import Github

with open("coreos-pygithub", "r") as f:
    token = f.read().strip()

start_date = datetime(2020, 1 , 1)
end_date = datetime(2020, 12, 31)

coreos_users = ["cgwalters",
                "dustymabe",
                "jlebon",
                "bgilbert",
                "mike-nguyen",
                "lucab",
                "ashcrow",
                "crawford",
                "jtligon",
                "imcleod",
                "darkmuggle",
                "arithx",
                "ravanelli",
                "cverna",
                "miabbott",
                "LorbusChris",
                "zonggen",
                "kelvinfan001",
                "bh7cw",
                "nikita-dubrovskii",
                "travier",
                "rfairley",
                "sohankunkerkar"]

g = Github(token)

coreos_repos = g.get_organization("coreos").get_repos(sort="updated")
# ostree_repos = g.get_organization("ostreedev").get_repos(sort="updated")

selected_repos = {}
for r in coreos_repos:
    if r.forks > 0:
        found = False
        commits = r.get_commits(since=start_date, until=end_date)
        issues = r.get_issues(since=start_date, state="closed")
        total_commits = 0
        total_issues = 0
        for c in commits:
            total_commits += 1
            if c.author is not None and c.author.login in coreos_users:
                print(r.name)
                found = True

        if found:
            for i in issues:
                total_issues += 1
            selected_repos[r.name] = [total_commits, total_issues]

print(selected_repos)
#all_authors = g.get_repo("coreos/coreos-assembler").get_collaborators()