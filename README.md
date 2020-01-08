# Design Studio Scheduler
A Python 3 utility for taking Doodle poll responses and uniquely assigning them to time shifts

## Installation
```
git clone https://github.com/vanderbilt-design-studio/scheduler/
virtualenv3 .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

## Usage
```
source .venv/bin/activate
# MANUAL STEP: add Doodle.xls poll responses file to the folder
python3 main.py
# MANUAL STEP: open the output Schedule.xls format, which will contain the shifts ordered by date
```
## How it works
### Libraries used
* cvxpy -- used for integer program calculations
* pandas -- used for reading and writing to Excel files

### Theory
The problem at hand is to take the mentors availabilities and assign them each a shift such that the number of shifts covered is maximized. It is reasonable to think of it as a maximum bipartite matching problem:

The input to the problem is a graph G with two sets of vertices V1 (the mentors), V2 (the shifts).
The only edges in the graph (mentor availabilities) are those between vertices in V1 and V2 -- there are no edges within the sets.
Some relations in such a graph will include one-to-many, many-to-one, one-to-one, one-to-none, etc.
The goal is to create the maximum number of pairs (fill the maximum number of shifts with the mentors we have).

I formulate this as an integer program (IP)
```
let E be the set of edges between V1, V2
let xe be a variable to indicate whether the edge e is on or off
let delta(v) be the set of edges adjacent to some vertex
max IP sum(xe in E) // Maximize the number of matchings
such that sum(xe for e in delta(v)) <= 1 // No vertex can have more than one adjacent edge
          xe binary
```
Which can be extended to include weights on edges that should be selected first (or in the context of this problem, you could set delta(some shift) to be higher so that shift would be occupied first, or some edges in delta(mentor) to indicate which shift(s) the mentor would prefer to have.

## TODOs

* [x] Support (OK) entries by weighting them half of "OK" in the objective function
* [x] Support multiple mentors per shift
    * [x] Barrier function for preferring >= 1 mentor per shift
* [ ] Support shift weighting
    * Can manually remove undesired shifts after first confirming an optimal assignment
* [ ] Resilience-to-change scheduling: when shift assignments will be optimal anyways, try to assign shifts so that if one person's availability changes, the entire schedule is not shifted around 
