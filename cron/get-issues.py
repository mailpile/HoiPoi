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
        'issues': ('%(indent)s<ol class="issues %(classes)s">\n'
                   '%(lines)s\n%(indent)s</ol>'),
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
        'issues': ('%(indent)s<ol class="issues %(classes)s">\n'
                   '%(lines)s\n%(indent)s</ol>'),
        'labels': ('%(indent)s<ul class="labels %(classes)s">\n'
                   '%(lines)s\n%(indent)s</ul>'),
        'stones': ('%(indent)s<ul class="milestones vote-list %(classes)s">\n'
                   '%(lines)s\n%(indent)s</ul>')
    },
    'hoipoi-ranked': {
        'issue': ('%(indent)s'
                  '<li class="issue %(classes)s"'
                  ' data-labels="%(labels)s"'
                  ' data-comments="%(comments)s"'
                  ' data-issue="%(number)s">'
                  '<h6 class="title">%(title)s</h6>'
                  ' <span class="summary">%(summary)s</span>'
                  ' <a class="more" href="%(url)s">see conversation</a>'
                  '</li>'),
        'label': '%(indent)s<li class="label %(classes)s">%(text)s</li>',
        'stone': '%(indent)s<li class="milestone %(classes)s">%(text)s</li>',
        'issues': ('%(indent)s<ol class="issues ranked-election %(classes)s" '
                   'data-election="%(unique_id)s">\n'
                   '%(lines)s\n%(indent)s</ol>'),
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


def clean_url(t):
    t = t.replace('"', '%22').replace("'", '%27')  # Breaks HTML
    t = t.replace('<', '%3C').replace('>', '%3E')  # Breaks HTML
    t = t.replace('(', '%28').replace(')', '%28')  # Breaks markdown
    t = t.replace('[', '%5B').replace(']', '%5D')  # Breaks markdown
    return t


def entity_encode(t):
    t = unicode(t)
    t = t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return t


def issue_lines(template, issues, pid,
                indent='', label_ignore=[], dedup=False):
    lines = []
    issues.sort(key=lambda i: i.title)
    for i in issues:
        if dedup and i in dedup:
            continue
        body = entity_encode(i.body)
        summary = body.split('\n')[0]
        labels = [l for l in i.labels if l.name.lower() not in label_ignore]
        lines.append(template['issue'] % {
            'indent': indent,
            'unique_id': '%s-%s' % (pid, entity_encode(i.number)),
            'classes': ' '.join(['label-%s' % html_class(l.name)
                                 for l in labels]),
            'labels': ', '.join([html_class(l.name) for l in labels]),
            'number': entity_encode(i.number),
            'url': clean_url(i.html_url),
            'title': entity_encode(i.title),
            'summary': summary,
            'comments': entity_encode(i.comments),
            'body': body,
            'text': entity_encode(i.title),
        })
        if dedup:
            dedup.append(i)
    return lines


def issue_list(template, issues, pid='all', indent='', **kwargs):
    data = '\n'.join(issue_lines(template, issues, pid,
                                 indent=indent+'   ', **kwargs))
    if not data:
        return ''
    return template['issues'] % {
        'indent': indent,
        'unique_id': '%s-issues' % pid,
        'classes': '',
        'lines': data
    }


def label_lines(template, issues, pid, indent='', label_want=None, **kwargs):
    by_label = {'Unlabeled': [None, []]}
    ignored = kwargs.get('label_ignore') or []
    for i in issues:
        labels = [l for l in i.labels
                  if (l.name.lower() not in ignored) and
                     ((not label_want) or l.name.lower() in label_want)]
        if not labels:
            by_label['Unlabeled'][1].append(i)
        for label in labels:
            if label.name not in by_label:
                by_label[label.name] = (label, [])
            by_label[label.name][1].append(i)

    lines = []
    for lname in sorted(by_label.keys()):
        label, issues = by_label[lname]
        uid = '%s-%s' % (pid, html_class(lname))
        data = issue_list(template, issues, pid=uid, indent=indent, **kwargs)
        if data:
            lines.append(template['label'] % {
                'indent': indent,
                'unique_id': uid,
                'classes': 'label-%s' % html_class(lname),
                'title': entity_encode(lname),
                'summary': '',  # FIXME
                'body': data,
                'text': entity_encode(lname) + ' ' + data
            })
    return lines


def label_list(template, issues,
               pid='all', indent='', label_want=None, **kwargs):
    data = '\n'.join(label_lines(template, issues, pid,
                                 indent=indent+'   ', label_want=label_want,
                                 **kwargs))
    if not data:
        return ''
    return template['labels'] % {
        'indent': indent,
        'unique_id': '%s-labels' % pid,
        'classes': '',
        'lines': data
    }


def milestone_lines(template, issues, roadmap_labels, pid,
                    indent='', **kwargs):
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
        uid = '%s-%s' % (pid, html_class(mname))
        data = label_list(template, issues,
                          pid=uid, indent=indent, label_want=roadmap_labels,
                          **kwargs)
        if data:
            lines.append(template['stone'] % {
                'indent': indent,
                'unique_id': uid,
                'classes': 'milestone-%s' % html_class(mname),
                'title': entity_encode(mname),
                'summary': '',  # FIXME
                'body': data,
                'text': entity_encode(mname) + ' ' + data
            })
    return lines


def milestone_list(template, issues, roadmap_labels,
                   pid='all', indent='', **kwargs):
    data = '\n'.join(milestone_lines(template, issues, roadmap_labels, pid,
                                     indent=indent+'   ', **kwargs))
    if not data:
        return ''
    return template['stones'] % {
        'indent': indent,
        'unique_id': '%s-milestones' % pid,
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
        label_ignore = []

    if '--milestone_filter' in sys.argv:
        stone_arg = sys.argv[sys.argv.index('--milestone_filter')+1]
        stone_filter = set([l.lower().strip() for l in stone_arg.split(',')])
        issues = issues or repo.get_issues(**issue_args)
        issues = [i for i in issues
                  if i.milestone and (i.milestone.name.lower() in stone_filter)]
    else:
        stone_filter = None

    if '--roadmap_labels' in sys.argv:
        label_arg = sys.argv[sys.argv.index('--roadmap_labels')+1]
        roadmap_labels = [l.lower().strip() for l in label_arg.split(',')]
    else:
        roadmap_labels = None

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
        safe_print(milestone_list(template, issues, roadmap_labels, **kwargs))

    if '-i' in sys.argv:
        run_shell()
except:
    traceback.print_exc()
    run_shell()
