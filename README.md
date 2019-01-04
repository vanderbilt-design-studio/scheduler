# Design Studio Scheduler
A Python 3 utility for taking Doodle poll responses and uniquely assigning them to time shifts

## Installation
```
git clone https://github.com/vanderbilt-design-studio/scheduler/
virtualenv3 .venv
source .venv/bin/activate
pip3 install requirements.txt
```

## Usage
```
source .venv/bin/activate
// MANUAL STEP: add Doodle.xls poll responses file to the folder
python3 main.py
// MANUAL STEP: open the output Schedule.xls format, which will contain the shifts in no particular order
```
## How it works
### Libraries used
* cvxpy -- used for integer program calculations
* pandas -- used for reading and writing to Excel files

### Theory
The problem at hand is to take the mentors availabilities and assign them each a shift such that the number of shifts covered is maximized. It is reasonable to think of it as a maximum bipartite matching problem:

The input to the problem is a graph G with two sets of vertices V1, V2.
The only edges in the graph are those between vertices in V1 and V2 (there are no edges within the sets).
Some relations in such a graph will include one-to-many, many-to-one, one-to-one, one-to-none, etc.
The goal is to create the maximum number of pairs.

I formulate this as an integer program (IP)
```
let E be the set of edges between V1, V2
let xe be a variable to indicate whether the edge e is on or off
let delta(v) be the set of edges adjacent to some vertex
max IP sum(xe in E) // Maximize the number of matchings
such that sum(xe for e in delta(v)) <= 1 // No vertex can have more than one adjacent edge
          xe binary
```
Which can be extended to include weights on edges that should be selected first.