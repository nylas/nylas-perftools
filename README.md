# Stackcollector

![Screenshot](/images/screenshot.png)

This is a basic utility for automatically collecting and visualizing profiles from distributed processes. It has two parts: a long-running collector agent that periodically gets samples from processes, and a frontend that serves visualizations. Data is timestamped and persisted using gdbm, allowing for time-based querying.

## Installation

```
# create a directory for data files
sudo mkdir -p /var/lib/stackcollector
sudo chmod a+rw /var/lib/stackcollector

# run services inside a virtualenv
virtualenv .
source bin/activate
python setup.py install
```

## Running the collector

The collector assumes that processes expose profiles in the [flamegraph line format](https://github.com/brendangregg/FlameGraph#2-fold-stacks) over HTTP. [Here's an example](https://github.com/nylas/sync-engine/blob/master/inbox/util/profiling.py) of how to implement that in Python.

```
# Every minute, gather stacks from a local process listening on port 16384.
python -m stackcollector.collector --host localhost -port 16384 --interval 60
```

## Running the visualizer

```
python -m stackcollector.visualizer --port 5555
```

Then visit e.g. `http://localhost:5555?from=-15minutes` to see data from the
past 15 minutes.
