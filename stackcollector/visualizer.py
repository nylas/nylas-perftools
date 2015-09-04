import influxdb
from flask import Flask, request, jsonify, render_template


app = Flask(__name__)
app.config['DEBUG'] = True
db_name = 'stacksdb'


def _build_query(from_, to):
    clauses = []
    if from_ is not None:
        clauses.append('time > {}s'.format(from_))

    if to is not None:
        clauses.append('time < {}s'.format(to))
    q = 'SELECT stack FROM stacksample'
    if clauses:
        q += ' WHERE '
        q += ' AND '.join(clauses)
    return q


class Node(object):
    def __init__(self, name):
        self.name = name
        self.value = 0
        self.children = {}

    def serialize(self, threshold=None):
        res = {
            'name': self.name,
            'value': self.value
        }
        if self.children:
            serialized_children = [
                child.serialize(threshold)
                for _, child in sorted(self.children.items())
                if child.value >= threshold
            ]
            if serialized_children:
                res['children'] = serialized_children
        return res

    def add_stack(self, frames, value):
        self.value += value
        if not frames:
            return
        head = frames[0]
        child = self.children.get(head)
        if child is None:
            child = Node(name=head)
            self.children[head] = child
        child.add_stack(frames[1:], value)


def from_raw(rawlines):
    root = Node('root')
    for line in rawlines:
        frames, value = line.split()
        frames = frames.split(';')
        try:
            value = int(value)
        except ValueError:
            continue
        root.add_stack(frames, value)
    return root


@app.route('/data')
def data():
    from_ = request.args.get('from')
    to = request.args.get('to')
    threshold = float(request.args.get('threshold', 0))

    client = influxdb.InfluxDBClient(database=db_name)
    resultset = client.query(_build_query(from_, to))
    stacks = [point['stack'] for point in resultset.get_points()]
    d = from_raw(stacks)
    return jsonify(d.serialize(threshold * d.value))


@app.route('/')
def render():
    return render_template('view.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9999)
