"""
Minimal instrumentation for visualizing Python code profiles using the
Chrome developer tools.
Example usage:
>>> profiler = Profiler()
>>> profiler.start()
>>> my_expensive_code()
>>> profiler.stop()
>>> with open('my.cpuprofile', 'w') as f:
...    f.write(profiler.output())

In a gevented environnment, context switches can make things confusing. Data
collection can be limited to a single greenlet by passing
>>> profiler = Profiler(target_greenlet = gevent.getcurrent())
"""
import json
import sys
import timeit

try:
    import gevent
except ImportError:
    gevent = None


class Node(object):

    def __init__(self, name, id_):
        self.name = name
        self.id_ = id_
        self.children = {}
        self.hitCount = 1

    def serialize(self):
        res = {
            'functionName': self.name,
            'hitCount': self.hitCount,
            'children': [c.serialize() for c in self.children.values()],
            'scriptId': '1',
            'url': '',
            'lineNumber': 1,
            'columnNumber': 1,
            'deoptReason': '',
            'id': self.id_,
            'callUID': self.id_
        }
        return res

    def add(self, frames, idgen):
        if not frames:
            self.hitCount += 1
            return
        head = frames[0]
        child = self.children.get(head)
        if child is None:
            child = Node(name=head, id_=idgen())
            self.children[head] = child
        child.add(frames[1:], idgen)


class Profiler(object):

    def __init__(self, target_greenlet=None, interval=0.0001):
        self.target_greenlet_id = (
            id(target_greenlet) if target_greenlet else None)
        self.interval = interval
        self.started = None
        self.last_profile = None
        self.root = Node('head', 1)
        self.nextId = 1
        self.samples = []
        self.timestamps = []

    def _idgenerator(self):
        self.nextId += 1
        return self.nextId

    def _profile(self, frame, event, arg):
        if event == 'call':
            self._record_frame(frame.f_back)

    def _record_frame(self, frame):
        if self.target_greenlet_id and id(gevent.getcurrent()) != self.target_greenlet_id:
            return
        now = timeit.default_timer()
        if self.last_profile is not None:
            if now - self.last_profile < self.interval:
                return
        self.last_profile = now
        self.timestamps.append(int(1e6 * now))
        stack = []
        while frame is not None:
            stack.append(self._format_frame(frame))
            frame = frame.f_back
        stack.reverse()
        self.root.add(stack, self._idgenerator)
        self.samples.append(self.nextId)

    def _format_frame(self, frame):
        return '{}({})'.format(frame.f_code.co_name,
                               frame.f_globals.get('__name__'))

    def output(self):
        if self.samples:
            data = {
                'startTime': self.started,
                'endTime': 0.000001 * self.timestamps[-1],
                'timestamps': self.timestamps,
                'samples': self.samples,
                'head': self.root.serialize()
            }
        else:
            data = {}
        return json.dumps(data)

    def start(self):
        sys.setprofile(self._profile)
        if not self.started:
            self.started = timeit.default_timer()

    def stop(self):
        sys.setprofile(None)
