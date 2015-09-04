import datetime
import time
import click
import requests
from nylas.logging import get_logger, configure_logging
from visualizer import Sample, db

configure_logging()
log = get_logger()


def collect(host, port, db_name, **connect_args):
    try:
        resp = requests.get('http://{}:{}?reset=true'.format(host, port))
        resp.raise_for_status()
    except (requests.ConnectionError, requests.HTTPError) as exc:
        log.warning('Error collecting data', error=exc, host=host, port=port)
        return
    data = resp.content.splitlines()
    elapsed = float(data[0].split()[1])
    granularity = float(data[1].split()[1])
    now = datetime.datetime.utcnow()
    sample = Sample(timestamp=now,
                    host=host,
                    port=port,
                    sample='\n'.join(data[2:]))
    try:
        db.session.add(sample)
        db.session.commit()
    except Exception as exc:
        log.warning('Error saving data', error=exc, host=host, port=port)
        return
    log.info('Data collected', host=host, port=port,
             num_stacks=len(data) - 2)


@click.command()
@click.option('--db', default='stacksdb')
@click.option('--host', '-h', multiple=True)
@click.option('--nprocs', '-n', type=int, default=1)
@click.option('--interval', '-i', type=int, default=60)
def run(db, host, nprocs, interval):
    while True:
        for h in host:
            for port in range(16384, 16384 + nprocs):
                collect(h, port, db)
        time.sleep(interval)


if __name__ == '__main__':
    run()
