from typing import List, Dict
from itertools import chain

import cvxpy as cp
import pandas as pd

doodle_df = pd.read_excel('Doodle.xls', skiprows=3, header=[0, 1, 2])

shifts = 0
mentors = []
for i, series in doodle_df.iterrows():
    if i == 'Count':
        break
    shifts = max(shifts, len(series))
    mentors.append([j for j, val in enumerate(series.tolist()) if val == 'OK'])

edges: List[List[cp.Variable]] = []
constraints: List[cp.Constant] = []

delta_shift: Dict[int, List[cp.Variable]] = {}
for shift in range(0, shifts):
    delta_shift[shift] = []

for mentor in mentors:
    mentor_edges = []
    for i in range(0, shifts):
        edge = cp.Variable(boolean=True)
        mentor_edges.append(edge)
        delta_shift[i].append(edge)
        if i not in mentor:
            constraints.append(edge == 0)
    edges.append(mentor_edges)

for delta in chain(delta_shift.values(), edges):
    if len(delta) > 0:
        constraints.append(cp.sum(delta) <= 1)

objective = 0
for mentor_edges in edges:
    for edge in mentor_edges:
        objective += edge
objective = cp.Maximize(objective)

problem = cp.Problem(objective, constraints)

print(f'Attempting to assign {shifts} shifts to {len(mentors)} mentors')
problem.solve()

if problem.status in ["infeasible", "unbounded"]:
    print(
        f'The solver has found the problem to be {problem.status}. Your input may be incorrectly formatted.')
else:
    print(
        f'Shifts have been assigned with an optimal assignment of {round(problem.value)}')
    out_df: Dict[str, str] = {}
    for i, (name, series) in enumerate(doodle_df.iterrows()):
        if name == 'Count':
            break
        
        active_edges = [j for j in range(0, shifts) if round(float(edges[i][j].value)) == 1]
        if len(active_edges) > 0:
            for active_edge in active_edges:
                out_df[series.keys()[active_edge]] = [name]
    out_df = pd.DataFrame(out_df)
    out_df.to_excel('Schedule.xls')
    print('They have been stored in Schedule.xls')

    

