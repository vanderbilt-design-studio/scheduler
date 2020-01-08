from typing import List, Dict, Tuple
from itertools import chain
from collections import OrderedDict, defaultdict
import math

import cvxpy as cp
import pandas as pd
import datetime

YEAR_MONTH_FORMAT = '%B %Y'
DAY_FORMAT = '%a %d'
TIME_FORMAT = '%I:%M:%S %p'
DOODLE_DATETIME_FORMAT = f"('{YEAR_MONTH_FORMAT}', '{DAY_FORMAT}') %I:%M %p"
MENTORS_PER_SHIFT_MAX = 2
SHIFTS_PER_MENTOR_MAX = 1


def parse_doodle_datetime(datetime_tup: Tuple[str]) -> datetime.datetime:
    time_separator_index = datetime_tup[2].index("–")
    time_start_str = datetime_tup[2][:time_separator_index].strip()
    time_end_str = datetime_tup[2][time_separator_index+1:].strip()
    datetime_start_str = f'{datetime_tup[0:2]} {time_start_str}'
    datetime_end_str = f'{datetime_tup[0:2]} {time_end_str}'
    return (datetime.datetime.strptime(datetime_start_str, DOODLE_DATETIME_FORMAT), datetime.datetime.strptime(datetime_end_str, DOODLE_DATETIME_FORMAT))

def is_mentor_available(response: str) -> bool:
    return response == '(OK)' or response == 'OK'

def response_to_weighting(response: str) -> int:
    if response == '(OK)':
        return 1
    elif response == 'OK':
        return 2
    else:
        return 0

DOODLE_DF: pd.DataFrame = pd.read_excel('Doodle.xls', skiprows=3, header=[0, 1, 2], skipfooter=1, index_col=0)

SHIFTS = 0
MENTORS_AVAILABILITY: List[List[int]] = []
MENTORS_WEIGHTING: List[List[int]] = []
for i, mentor_responses in DOODLE_DF.iterrows():
    SHIFTS = max(SHIFTS, len(mentor_responses))
    MENTORS_AVAILABILITY.append([j for j, response in enumerate(mentor_responses.tolist()) if is_mentor_available(response)])
    MENTORS_WEIGHTING.append([response_to_weighting(response) for response in mentor_responses.tolist()])

MENTORS_EDGES: List[List[cp.Variable]] = []
CONSTRAINTS: List[cp.Constant] = []

shifts_edges: Dict[int, List[cp.Variable]] = defaultdict(list)

for mentor_availability in MENTORS_AVAILABILITY:
    mentor_edges = []
    for shift in range(SHIFTS):
        edge = cp.Variable(boolean=True)
        mentor_edges.append(edge)
        shifts_edges[shift].append(edge)
        if shift not in mentor_availability:
            CONSTRAINTS.append(edge == 0) # Don't give a mentor a shift they are unavailable for
    MENTORS_EDGES.append(mentor_edges)

for shift_edges in shifts_edges.values():
    if len(shift_edges) > 0:
        CONSTRAINTS.append(cp.sum(shift_edges) <= MENTORS_PER_SHIFT_MAX)

for mentor_edges in MENTORS_EDGES:
    if len(mentor_edges) > 0:
        CONSTRAINTS.append(cp.sum(mentor_edges) <= SHIFTS_PER_MENTOR_MAX) # Maximum of 1 shift per mentor

OBJECTIVE = 0
for mentor_weighting, mentor_edges in zip(MENTORS_WEIGHTING, MENTORS_EDGES):
    for weighting, edge in zip(mentor_weighting, mentor_edges):
        OBJECTIVE += weighting * edge # Give priority to a mentor's preferences "(OK) = 1, OK = 2, NO = 0".

for shift_edges in shifts_edges.values():
    OBJECTIVE += -100 * cp.abs(cp.sum(shift_edges) - 1)

# Maximize the weighted mentor availability
OBJECTIVE = cp.Maximize(OBJECTIVE)

# Formulate the linear optimization problem.
PROBLEM = cp.Problem(OBJECTIVE, CONSTRAINTS)

print(f'Attempting to assign {SHIFTS} shifts to {len(MENTORS_AVAILABILITY)} mentors')
PROBLEM.solve()

if PROBLEM.status in ["infeasible", "unbounded"]:
    print(f'The solver has found the problem to be {PROBLEM.status}. Your input may be incorrectly formatted.')
else:
    print(f'Shifts have been assigned with an optimal assignment of {round(PROBLEM.value)}')
    assignments: List[Tuple[datetime.datetime, str]] = []
    names: List[str] = []

    for shift, shift_datetime_key in enumerate(DOODLE_DF.keys()):
        assigned_mentors = [mentor for mentor in range(len(MENTORS_AVAILABILITY)) if round(float(MENTORS_EDGES[mentor][shift].value)) == 1]        
        
        for mentor in assigned_mentors:
            names.append(DOODLE_DF.index[mentor])
        if len(assigned_mentors) == 0: # Shift was not assigned to anybody
            names.append('N/A')
            assigned_mentors.append(-1)

        shift_start, shift_end = parse_doodle_datetime(shift_datetime_key)
        shift_duration = shift_end - shift_start
        for mentor in assigned_mentors:
            assignments.append((shift_start.strftime('%A'), shift_start.strftime(TIME_FORMAT), str(shift_duration), shift_end.strftime(TIME_FORMAT), shift_start))
    
    assignments = sorted(assignments, key=lambda assignment: assignment[-1])
    out_df = pd.DataFrame.from_dict(list(assignments))
    out_df.index = names
    out_df.columns = ['Day of Week', 'Start', 'Duration', 'End', 'Start Datetime']
    out_df.to_excel('Schedule.xls')
    print('They have been stored in Schedule.xls')
