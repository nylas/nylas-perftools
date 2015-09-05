import datetime
import time
import click
import requests
from nylas.logging import get_logger, configure_logging
from visualizer import Sample, db

configure_logging()
log = get_logger()


def collect(host, port, bucket_delta):
    try:
        resp = requests.get('http://{}:{}?reset=true'.format(host, port))
        resp.raise_for_status()
    except (requests.ConnectionError, requests.HTTPError) as exc:
        log.warning('Error collecting data', error=exc, host=host, port=port)
        return
    data = resp.content.splitlines()
    try:
        save(data, db, bucket_delta)
    except Exception as exc:
        log.warning('Error saving data', error=exc, host=host, port=port)
        return
    log.info('Data collected', host=host, port=port,
             num_stacks=len(data) - 2)


def save(data, host, port, db, bucket_delta):
    now = datetime.datetime.utcnow()
    i = 0
    for line in data[2:]:
        try:
            stack, value = line.split()
            value = int(value)
        except ValueError:
            continue


        sample = Sample.query.filter(Sample.stack == stack,
                                     Sample.end > now).first()
        if sample:
            sample.count += value
        else:
            sample = Sample(stack=stack,
                            start=now,
                            end=now + bucket_delta,
                            count=value,
                            host=host,
                            port=port)
        db.session.add(sample)
        print i
        i+= 1
    db.session.commit()


@click.command()
@click.option('--db', default='stacksdb')
@click.option('--host', '-h', multiple=True)
@click.option('--nprocs', '-n', type=int, default=1)
@click.option('--interval', '-i', type=int, default=60)
@click.option('--bucket', type=int, default=900)
def run(db, host, nprocs, interval, bucket):
    bucket_delta = datetime.timedelta(seconds=bucket)
    while True:
        for h in host:
            for port in range(16384, 16384 + nprocs):
                collect(h, port, db, bucket_delta)
        time.sleep(interval)


if __name__ == '__main__':
    run()
