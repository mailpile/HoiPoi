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


def issue_lines(template, issues, indent='', label_ignore=[], dedup=False):
    lines = []
    issues.sort(key=lambda i: i.title)
    for i in issues:
        if dedup and i in dedup:
            continue
        lines.append(template['issue'] % {
            'indent': indent,
            'classes': ' '.join(['label-%s' % html_class(l.name)
                                 for l in i.labels
                                 if l.name.lower() not in label_ignore]),
            'number': i.number,
            'text': i.title,
            'url': i.html_url
        })
        if dedup:
            dedup.append(i)
    return lines


def issue_list(template, issues, indent='', **kwargs):
    data = '\n'.join(issue_lines(template, issues,
                                 indent=indent+'   ', **kwargs))
    if not data:
        return ''
    return template['issues'] % {
        'indent': indent,
        'classes': '',
        'lines': data
    }


def label_lines(template, issues, indent='', **kwargs):
    by_label = {'Unlabeled': [None, []]}
    ignored = kwargs.get('label_ignore') or []
    for i in issues:
        labels = [l for l in i.labels if l.name.lower() not in ignored]
        if not labels:
            by_label['Unlabeled'][1].append(i)
        for label in labels:
            if label.name not in by_label:
                by_label[label.name] = (label, [])
            by_label[label.name][1].append(i)

    lines = []
    for lname in sorted(by_label.keys()):
        label, issues = by_label[lname]
        data = issue_list(template, issues, indent=indent, **kwargs)
        if data:
            lines.append(template['label'] % {
                'indent': indent,
                'classes': 'label-%s' % html_class(lname),
                'text': lname + ' ' + data
            })
    return lines


def label_list(template, issues, indent='', **kwargs):
    data = '\n'.join(label_lines(template, issues,
                                 indent=indent+'   ', **kwargs))
    if not data:
        return ''
    return template['labels'] % {
        'indent': indent,
        'classes': '',
        'lines': data
    }


def milestone_lines(template, issues, indent='', **kwargs):
    by_milestone = {}
    for i in issues:
        milestone = i.milestone
        mname = milestone.title if milestone else 'No Milestone'
        if mname.lower() in (kwargs.get('stone_ignore') or []):
            continue
        if mname not in by_milestone:
            by_milestone[mname] = (milestone, [])
        by_milestone[mname][1].append(i)

    lines = []
    for mname in sorted(by_milestone.keys()):
        milestone, issues = by_milestone[mname]
        data = label_list(template, issues, indent=indent, **kwargs)
        if data:
            lines.append(template['stone'] % {
                'indent': indent,
                'classes': 'milestone-%s' % html_class(mname),
                'text': mname + ' ' + data
            })
    return lines


def milestone_list(template, issues, indent='', **kwargs):
    data = '\n'.join(milestone_lines(template, issues,
                                     indent=indent+'   ', **kwargs))
    if not data:
        return ''
    return template['stones'] % {
        'indent': indent,
        'classes': '',
        'lines': data
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

    issues = None
    if '--all' in sys.argv:
        issue_args = {}
    elif '--closed' in sys.argv:
        issue_args = {'state': 'closed'}
    else:
        issue_args = {'state': 'open'}

    if '--label_filter' in sys.argv:
        label_arg = sys.argv[sys.argv.index('--label_filter')+1]
        label_filter = [l.lower().strip() for l in label_arg.split(',')]
        issue_args['labels'] = label_filter
    else:
        label_filter = None

    if '--label_ignore' in sys.argv:
        label_arg = sys.argv[sys.argv.index('--label_ignore')+1]
        label_ignore = [l.lower().strip() for l in label_arg.split(',')]
    else:
        label_ignore = None

    if '--milestone_filter' in sys.argv:
        stone_arg = sys.argv[sys.argv.index('--milestone_filter')+1]
        stone_filter = set([l.lower().strip() for l in stone_arg.split(',')])
        issues = issues or repo.get_issues(**issue_args)
        issues = [i for i in issues
                  if i.milestone and (i.milestone.name.lower() in stone_filter)]
    else:
        stone_filter = None

    kwargs = {
        'dedup': ['yup'] if '--dedup' in sys.argv else False,
        'label_ignore': label_ignore
    }
    if '--issues' in sys.argv:
        issues = issues or repo.get_issues(**issue_args)
        safe_print(issue_list(template, issues, **kwargs))

    if '--labels' in sys.argv:
        issues = issues or repo.get_issues(**issue_args)
        safe_print(label_list(template, issues, **kwargs))

    if '--roadmap' in sys.argv:
        issues = issues or repo.get_issues(**issue_args)
        safe_print(milestone_list(template, issues, **kwargs))

    if '-i' in sys.argv:
        run_shell()
except:
    traceback.print_exc()
    run_shell()
