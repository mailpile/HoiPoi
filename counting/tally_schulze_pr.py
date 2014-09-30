#!/usr/bin/python
#
#  Calculate election results on an open-ordering ballot 
#  using the Schulze Proportional Representation method.
#

from pyvotecore.schulze_pr import SchulzePR
import os
import json

JSON_HOME = '/home/mailpile/hoipoi/db/'
electionid = 1

# Collect all ballots from user JSON files
ballots = []
for json_file in os.listdir(JSON_HOME):
    if ".json" not in json_file:
        continue
    json_path = os.path.join(JSON_HOME, json_file)
    data = json.load(open(json_path, 'r'))
    ballot = data.get("election.%d" % (electionid), "").split(",")
    if ballot != []:
        ballots.append(ballot)

# Tally ballots
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
result = SchulzePR(tally, ballot_notation = "grouping").as_dict()

print result["order"]
