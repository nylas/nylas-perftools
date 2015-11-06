import time
from stacksampler import Sampler


def slp():
    time.sleep(0.00001)


def fn():
    for i in range(50000):
        slp()


s = Sampler()


def test_foo():
    s.start()
    fn()
    print s.output_stats()


if __name__ == '__main__':
    test_foo()
