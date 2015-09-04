from flask import Flask, request, jsonify, render_template
from flask.ext.sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = ('postgresql+psycopg2://'
                                         'test:test@localhost/test')

db = SQLAlchemy(app)


class Sample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True)
    host = db.Column(db.String(255))
    port = db.Column(db.Integer)
    sample = db.Column(db.Text)


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

    def add_raw(self, line):
        frames, value = line.split()
        frames = frames.split(';')
        try:
            value = int(value)
        except ValueError:
            return
        self.add_stack(frames, value)


@app.route('/data')
def data():
    from_ = request.args.get('from')
    to = request.args.get('to')
    host = request.args.get('host')
    threshold = float(request.args.get('threshold', 0))
    root = Node('root')
    # TODO(emfree): batch result rows
    for sample in Sample.query.all():
        stacks = sample.sample.split('\n')
        for stack in stacks:
            root.add_raw(stack)
    return jsonify(root.serialize(threshold * root.value))


@app.route('/')
def render():
    return render_template('view.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9999)
