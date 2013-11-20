from flask import Flask, render_template, url_for, request, jsonify
from top_stations import get_recs

app = Flask(__name__)

@app.route('/_get_stations', methods=['GET','POST'])
def get_stations():

    empty = request.form['empty']

    if empty == 'empty':
        color = '#CB181D'
    else:
        color = '#74A9CF'

    clean_recs, markers = [], []
    recs = get_recs(empty)
    for i in recs:
        clean_recs.append({
            'Station': i[0],
            'Percent Full': round((i[3] - i[2])/float(i[3])*100, 1),
            })
        markers.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [i[5], i[4]]
            },
            'properties': {
                'title': i[0],
                'description': str(i[3] - i[2]) + ' available bikes.',
                'marker-size': 'medium',
                'marker-color': color
            }
        })
    if empty == 'empty':
        return jsonify(recs = sorted(clean_recs), markers = markers)
    else:
        return jsonify(recs = sorted(clean_recs, reverse=True), markers=markers)


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
