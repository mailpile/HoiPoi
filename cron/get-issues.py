#!/usr/bin/env python
import code
import getpass
import re
import readline
import sys
import traceback

import PyGithub

username = 'BjarniRunar'
password = getpass.getpass('Password for %s: ' % username)
reponame = 'pagekite/Mailpile'


TEMPLATES = {
    'markdown': {
        'issue': '%(indent)s* [%(text)s](%(url)s)',
        'label': '%(indent)s* %(text)s',
        'stone': '%(indent)s* %(text)s',
        'issues': '%(lines)s',
        'labels': '%(lines)s',
        'stones': '%(lines)s'
    },
    'html': {
        'issue': ('%(indent)s<li class="issue %(classes)s">'
                  '<a href="%(url)s">%(text)s</a></li>'),
        'label': '%(indent)s<li class="label %(classes)s">%(text)s</li>',
        'stone': '%(indent)s<li class="milestone %(classes)s">%(text)s</li>',
        'issues': ('%(indent)s<ul class="issues %(classes)s">\n'
                   '%(lines)s\n%(indent)s</ul>'),
        'labels': ('%(indent)s<ul class="labels %(classes)s">\n'
                   '%(lines)s\n%(indent)s</ul>'),
        'stones': ('%(indent)s<ul class="milestones %(classes)s">\n'
                   '%(lines)s\n%(indent)s</ul>')
    },
    'hoipoi': {
        'issue': ('%(indent)s'
                  '<li class="issue %(classes)s" data-issue="%(number)s">'
                  '<a href="%(url)s">%(text)s</a></li>'),
        'label': '%(indent)s<li class="label %(classes)s">%(text)s</li>',
        'stone': '%(indent)s<li class="milestone %(classes)s">%(text)s</li>',
        'issues': ('%(indent)s<ul class="issues %(classes)s">\n'
                   '%(lines)s\n%(indent)s</ul>'),
        'labels': ('%(indent)s<ul class="labels %(classes)s">\n'
                   '%(lines)s\n%(indent)s</ul>'),
        'stones': ('%(indent)s<ul class="milestones vote-list %(classes)s">\n'
                   '%(lines)s\n%(indent)s</ul>')
    }
}


RE_HTML_CLASS_ILLEGAL = re.compile('[^a-z0-9_-]+')

def html_class(text):
    return re.sub(RE_HTML_CLASS_ILLEGAL, '_', text.lower())


def safe_print(text):
    print text.encode('utf-8')


def issue_lines(template, issues, indent=''):
    lines = []
    issues.sort(key=lambda i: i.title)
    for i in issues:
        lines.append(template['issue'] % {
           'indent': indent,
           'classes': '', # FIXME: Add all the labels as classes?
           'number': i.number,
           'text': i.title,
           'url': i.html_url
        })
    return lines


def issue_list(template, issues, indent=''):
    return template['issues'] % {
        'indent': indent,
        'classes': '',
        'lines': '\n'.join(issue_lines(template, issues, indent=indent+'   '))
    }


def label_lines(template, issues, indent=''):
    by_label = {}
    for i in issues:
        for label in i.labels:
            if label.name not in by_label:
                by_label[label.name] = (label, [])
            by_label[label.name][1].append(i)

    lines = []
    for lname in sorted(by_label.keys()):
        label, issues = by_label[lname]
        text = lname + ' ' + issue_list(template, issues, indent=indent)
        lines.append(template['label'] % {
            'indent': indent,
            'classes': 'label-%s' % html_class(lname),
            'text': text
        })
    return lines


def label_list(template, issues, indent=''):
    return template['labels'] % {
        'indent': indent,
        'classes': '',
        'lines': '\n'.join(label_lines(template, issues, indent=indent+'   '))
    }


def milestone_lines(template, issues, indent=''):
    by_milestone = {}
    for i in issues:
        milestone = i.milestone
        mname = milestone.title if milestone else 'Misc'
        if mname not in by_milestone:
            by_milestone[mname] = (milestone, [])
        by_milestone[mname][1].append(i)

    lines = []
    for mname in sorted(by_milestone.keys()):
        milestone, issues = by_milestone[mname]
        text = mname + ' ' + label_list(template, issues, indent=indent)
        lines.append(template['stone'] % {
            'indent': indent,
            'classes': 'milestone-%s' % html_class(mname),
            'text': text
        })
    return lines


def milestone_list(template, issues, indent=''):
    return template['stones'] % {
        'indent': indent,
        'classes': '',
        'lines': '\n'.join(milestone_lines(template, issues,
                                           indent=indent+'   '))
    }


def run_shell():
    variables = globals()
    code.InteractiveConsole(locals=variables).interact('Hello Github!')


try:
    gh = PyGithub.BlockingBuilder().Login(username, password).Build()
    repo = gh.get_repo(reponame)

    template = TEMPLATES['markdown']
    for tid, tpl in TEMPLATES.iteritems():
        if '--%s' % tid in sys.argv:
            template = tpl

    if '--all' in sys.argv:
        issues = repo.get_issues()
    elif '--closed' in sys.argv:
        issues = repo.get_issues(state='closed')
    else:
        issues = []

    if '--issues' in sys.argv:
        issues = issues or repo.get_issues(state='open')
        safe_print(issue_list(template, issues))

    if '--labels' in sys.argv:
        issues = issues or repo.get_issues(state='open')
        safe_print(label_list(template, issues))

    if '--roadmap' in sys.argv:
        issues = issues or repo.get_issues(state='open')
        safe_print(milestone_list(template, issues))

    if '-i' in sys.argv:
        run_shell()
except:
    traceback.print_exc()
    run_shell()
