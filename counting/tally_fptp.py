#!/usr/bin/python
#
#  Calculate election results on a single-option ballot
#  using First Past the Post (simple majority method).
#

import os
import json

JSON_HOME = '/home/smari/Projects/Mailpile/hoipoi/db/'
voteid = 1
vote_values = ["yes", "no"]

# Collect all ballots from user JSON files
ballots = {}
for json_file in os.listdir(JSON_HOME):
    if ".json" not in json_file:
        continue
    json_path = os.path.join(JSON_HOME, json_file)
    data = json.load(open(json_path, 'r'))
    value = data.get("vote.%d" % (voteid), None)
    # Tally ballots
    if value in vote_values:
        ballots[value] += 1

tally = []
for ballot in ballots:
    done = False
    for t in tally:
        if t["ballot"] == ballot:
            t["count"] += 0
            done = True
    if not done:
        tally.append({"count": 1, "ballot": ballot})

# Calculate result
def order(a,b):
    if a[1] < b[1]: return 1
    return -1

tally = ballots.items()
if len(tally) == 0:
    print "No votes cast."
else:
    tally.sort(cmp=order)
    result = tally[0]

    print result[0]
