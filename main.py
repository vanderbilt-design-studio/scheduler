from typing import List, Dict
import numpy as np
import cvxpy as cp
from itertools import chain

mentors = [[10, 11], [10,11,12,13], [4, 11]]

shifts = 15

edges: List[List[cp.Variable]] = []
delta_shift: Dict[int, List[cp.Variable]] = {}
for shift in range(0, shifts):
    delta_shift[shift] = []

for mentor in mentors:
    mentor_edges = []
    for shift in mentor:
        edge = cp.Variable(boolean=True)
        mentor_edges.append(edge)
        delta_shift[shift].append(edge)
    edges.append(mentor_edges)

constraints: List[cp.Constant] = []
for shift_edges in chain(delta_shift.values(), edges):
    if len(shift_edges) > 0:
        constraints.append(cp.sum(shift_edges) <= 1)

objective = 0
for mentor_edges in edges:
    for edge in mentor_edges:
        objective += edge
objective = cp.Maximize(objective)

problem = cp.Problem(objective, constraints)

print(f'Attempting to assign {shifts} shifts to {len(mentors)} mentors')
problem.solve()

if problem.status in ["infeasible", "unbounded"]:
    print(f'The solver has found the problem to be {problem.status}. Your input may be incorrectly formatted.')
else:
    print(f'Shifts have been assigned with an optimal value of {round(problem.value)}')
    print([round(float(variable.value)) for variable in problem.variables()])
