import subprocess
import influxdb
from flask import Flask, request


app = Flask(__name__)
app.config['DEBUG'] = True
db_name = 'stacksdb'


def _build_query(from_, to):
    if from_ is not None:
        from_clause = 'time > {}s'.format(from_)

    if to is not None:
        to_clause = 'time < {}s'.format(to)
    q = 'SELECT stacks FROM stacks'
    if from_ or to:
        q += ' WHERE '
        q += ' AND '.join(from_clause, to_clause)
    return q


@app.route('/')
def render():
    from_ = request.args.get('from')
    to = request.args.get('to')

    client = influxdb.InfluxDBClient(database=db_name)
    resultset = client.query(_build_query(from_, to))
    stacks = '\n'.join(point['stacks'] for point in resultset.get_points())
    p = subprocess.Popen('./flamegraph.pl', stdout=subprocess.PIPE,
                         stdin=subprocess.PIPE)
    ret = p.communicate(stacks)
    return ret


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9999)
