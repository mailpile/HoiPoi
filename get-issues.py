#!/usr/bin/env python
import code
import getpass
import readline
import sys
import traceback

import PyGithub

username = 'BjarniRunar'
password = getpass.getpass('Password for %s: ' % username)
reponame = 'pagekite/Mailpile'


def print_issues_markdown(issues, indent=''):
    issues.sort(key=lambda i: i.title)
    for i in issues:
        print '%s* [%s](%s)' % (indent, i.title, i.url)


def print_labels_markdown(issues, indent=''):
    by_label = {}
    for i in issues:
        for label in i.labels:
            if label.name not in by_label:
                by_label[label.name] = (label, [])
            by_label[label.name][1].append(i)

    for lname in sorted(by_label.keys()):
        label, issues = by_label[lname]
        print '%s* [%s](%s)' % (indent, lname, label.url)
        print_issues_markdown(issues, indent=indent+'   ')


def print_roadmap_markdown(issues, indent=''):
    by_milestone = {}
    for i in issues:
        milestone = i.milestone
        mname = milestone.title if milestone else 'Misc'
        if mname not in by_milestone:
            by_milestone[mname] = (milestone, [])
        by_milestone[mname][1].append(i)

    for mname in sorted(by_milestone.keys()):
        milestone, issues = by_milestone[mname]
        if milestone:
            print '%s* [%s](%s)' % (indent, mname, milestone.url)
        else:
            print '%s* %s' % (indent, mname)
        print_labels_markdown(issues, indent=indent+'   ')


def run_shell():
    variables = globals()
    code.InteractiveConsole(locals=variables).interact('Hello Github!')


try:
    gh = PyGithub.BlockingBuilder().Login(username, password).Build()
    repo = gh.get_repo(reponame)

    if '--all' in sys.argv:
        issues = repo.get_issues()
    elif '--closed' in sys.argv:
        issues = repo.get_issues(state='closed')
    else:
        issues = []

    if '--issues' in sys.argv:
        issues = issues or repo.get_issues(state='open')
        print_issues_markdown(issues)

    if '--labels' in sys.argv:
        issues = issues or repo.get_issues(state='open')
        print_labels_markdown(issues)

    if '--roadmap' in sys.argv:
        issues = issues or repo.get_issues(state='open')
        print_roadmap_markdown(issues)

    if '-i' in sys.argv:
        run_shell()
except:
    traceback.print_exc()
    run_shell()
