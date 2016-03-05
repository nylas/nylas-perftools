"""
Statistical profiling for long-running Python processes. This was built to work
with gevent, but would probably work if you ran the emitter in a separate OS
thread too.

Example usage
-------------
Add
>>> gevent.spawn(run_profiler, '0.0.0.0', 16384)

in your program to start the profiler, and run the emitter in a new greenlet.
Then curl localhost:16384 to get a list of stack frames and call counts.
"""

from __future__ import print_function
import sys
import atexit
import collections
import signal
import time
from werkzeug.serving import BaseWSGIServer, WSGIRequestHandler
from werkzeug.wrappers import Request, Response
try:
    from nylas.logging import get_logger
    logger = get_logger()
except ImportError:
    class _Logger(object):
        def info(msg):
            print(msg, file=sys.stderr)
    logger = _Logger()


class Sampler(object):
    """
    A simple stack sampler for low-overhead CPU profiling: samples the call
    stack every `interval` seconds and keeps track of counts by frame. Because
    this uses signals, it only works on the main thread.
    """
    def __init__(self, interval=0.005):
        self.interval = interval
        self._started = None
        self._stack_counts = collections.defaultdict(int)

    def start(self):
        self._started = time.time()
        try:
            signal.signal(signal.SIGVTALRM, self._sample)
        except ValueError:
            raise ValueError('Can only sample on the main thread')

        signal.setitimer(signal.ITIMER_VIRTUAL, self.interval)
        atexit.register(self.stop)

    def _sample(self, signum, frame):
        stack = []
        while frame is not None:
            stack.append(self._format_frame(frame))
            frame = frame.f_back

        stack = ';'.join(reversed(stack))
        self._stack_counts[stack] += 1
        signal.setitimer(signal.ITIMER_VIRTUAL, self.interval)

    def _format_frame(self, frame):
        return '{}({})'.format(frame.f_code.co_name,
                               frame.f_globals.get('__name__'))

    def output_stats(self):
        if self._started is None:
            return ''
        elapsed = time.time() - self._started
        lines = ['elapsed {}'.format(elapsed),
                 'granularity {}'.format(self.interval)]
        ordered_stacks = sorted(self._stack_counts.items(),
                                key=lambda kv: kv[1], reverse=True)
        lines.extend(['{} {}'.format(frame, count)
                      for frame, count in ordered_stacks])
        return '\n'.join(lines) + '\n'

    def reset(self):
        self._started = time.time()
        self._stack_counts = collections.defaultdict(int)

    def stop(self):
        self.reset()
        signal.setitimer(signal.ITIMER_VIRTUAL, 0)

    def __del__(self):
        self.stop()


class Emitter(object):
    """A really basic HTTP server that listens on (host, port) and serves the
    process's profile data when requested. Resets internal sampling stats if
    reset=true is passed."""
    def __init__(self, sampler, host, port):
        self.sampler = sampler
        self.host = host
        self.port = port

    def handle_request(self, environ, start_response):
        stats = self.sampler.output_stats()
        request = Request(environ)
        if request.args.get('reset') in ('1', 'true'):
            self.sampler.reset()
        response = Response(stats)
        return response(environ, start_response)

    def run(self):
        server = BaseWSGIServer(self.host, self.port, self.handle_request,
                                _QuietHandler)
        server.log = lambda *args, **kwargs: None
        logger.info('Serving profiles on port {}'.format(self.port))
        server.serve_forever()


class _QuietHandler(WSGIRequestHandler):
    def log_request(self, *args, **kwargs):
        """Suppress request logging so as not to pollute application logs."""
        pass


def run_profiler(host='0.0.0.0', port=16384):
    sampler = Sampler()
    sampler.start()
    e = Emitter(sampler, host, port)
    e.run()
