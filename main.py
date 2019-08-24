from typing import List, Dict, Tuple
from itertools import chain
from collections import OrderedDict

import cvxpy as cp
import pandas as pd
import datetime

DOODLE_DATETIME_FORMAT = "('%B %Y', '%a %d', '%I:%M %p"
OUTPUT_DATETIME_FORMAT = "%B %Y %a %d %I:%M %p"


def parse_doodle_datetime(datetime_str: str) -> datetime.datetime:
    datetime_str = datetime_str[:datetime_str.index(" –")]
    return datetime.datetime.strptime(datetime_str, DOODLE_DATETIME_FORMAT)


DOODLE_DF = pd.read_excel('Doodle.xls', skiprows=3, header=[0, 1, 2], skipfooter=1, index_col=0)

SHIFTS = 0
MENTORS = []
MENTORS_WEIGHTING = []
for i, series in DOODLE_DF.iterrows():
    SHIFTS = max(SHIFTS, len(series))
    MENTORS.append([j for j, val in enumerate(series.tolist()) if val == 'OK' or val == '(OK)'])
    MENTORS_WEIGHTING.append([1 if val == '(OK)' else 2 if val == 'OK' else 0 for val in series.tolist()])

EDGES: List[List[cp.Variable]] = []
CONSTRAINTS: List[cp.Constant] = []

delta_shift: Dict[int, List[cp.Variable]] = {shift: [] for shift in range(SHIFTS)}

for mentor in MENTORS:
    mentor_edges = []
    for i in range(SHIFTS):
        edge = cp.Variable(boolean=True)
        mentor_edges.append(edge)
        delta_shift[i].append(edge)
        if i not in mentor:
            CONSTRAINTS.append(edge == 0)
    EDGES.append(mentor_edges)

for delta in chain(delta_shift.values(), EDGES):
    if len(delta) > 0:
        CONSTRAINTS.append(cp.sum(delta) <= 1)

OBJECTIVE = 0
for mentor_weighting, mentor_edges in zip(MENTORS_WEIGHTING, EDGES):
    for weighting, edge in zip(mentor_weighting, mentor_edges):
        OBJECTIVE += weighting * edge
OBJECTIVE = cp.Maximize(OBJECTIVE)

PROBLEM = cp.Problem(OBJECTIVE, CONSTRAINTS)

print(f'Attempting to assign {SHIFTS} shifts to {len(MENTORS)} mentors')
PROBLEM.solve()

if PROBLEM.status in ["infeasible", "unbounded"]:
    print(
        f'The solver has found the problem to be {PROBLEM.status}. Your input may be incorrectly formatted.')
else:
    print(
        f'Shifts have been assigned with an optimal assignment of {round(PROBLEM.value)}')
    assignments: List[Tuple[datetime.datetime, str]] = []

    for i, (name, series) in enumerate(DOODLE_DF.iterrows()):
        active_edges = [j for j in range(SHIFTS) if round(float(EDGES[i][j].value)) == 1]
        if len(active_edges) > 0:
            for active_edge in active_edges:
                shift_datetime_str = str(series.keys()[active_edge])
                assignments.append((shift_datetime_str, name))
    for key in series.keys():
        if str(key) not in map(lambda assignment: assignment[0], assignments):
            assignments.append((str(key), 'N/A'))
    assignments = sorted(
        assignments, key=lambda assignment: parse_doodle_datetime(assignment[0]))
    out_df = pd.DataFrame.from_dict(list(assignments))
    out_df.to_excel('Schedule.xls')
    print('They have been stored in Schedule.xls')
