import time
import click
import requests
import influxdb
from nylas.logging import get_logger, configure_logging

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
    points = []
    for ind, stack in enumerate(data[2:]):
        points.append({
            'measurement': 'stacksample',
            'tags': {
                'host': host,
                'port': port,
                'seq': ind,
            },
            'fields': {
                'stack': stack,
                'elapsed': elapsed,
                'granularity': granularity
            }
        })
    try:
        client = influxdb.InfluxDBClient(database=db_name, **connect_args)
        client.write_points(points)
    except (influxdb.exceptions.InfluxDBClientError,
            influxdb.exceptions.InfluxDBServerError) as exc:
        log.warning('Error saving data', error=exc, host=host, port=port)
        return
    log.info('Data collected', host=host, port=port)


@click.command()
@click.option('--db', default='stacksdb')
@click.option('--host', '-h', multiple=True)
@click.option('--nprocs', '-n', type=int, default=1)
@click.option('--interval', '-i', type=int, default=60)
def run(db, host, nprocs, interval):
    try:
        client = influxdb.InfluxDBClient()
        client.create_database(db)
    except influxdb.exceptions.InfluxDBClientError:
        pass

    while True:
        for h in host:
            for port in range(16384, 16384 + nprocs):
                collect(h, port, db)
        time.sleep(interval)


if __name__ == '__main__':
    run()
