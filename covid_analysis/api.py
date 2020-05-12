import json

import flask
import plotly
from flask_socketio import SocketIO

from .data_analysis import get_country_data, process_covid_data
from .data_utils import fetch_latest_cases_data
from .gmm_modelling import predict_peaks_using_gmm, plot_peaks
from .plotting_utils import construct_y_axis_title

app = flask.Flask(__name__)
app.config['SECRET_KEY'] = '10'
socketio = SocketIO(app)


@app.route('/', methods=['GET'])
def index():
    return 'Welcome to this site containing information about COVID'


@app.route('/countries/<string:country_name>', methods=['GET'])
def get_countries(country_name: str):
    country_figure = get_country_data(country_name)
    y_axis_title = construct_y_axis_title(
        'deaths, infections and cases',
        get_daily_change=False,
        get_rolling_average=False,
        normalise_by_population=False,
    )
    country_figure.update_yaxes(title={'text': y_axis_title})
    country_figure = json.dumps(country_figure, cls=plotly.utils.PlotlyJSONEncoder)
    return flask.render_template(
        'index.html',
        plot=country_figure,
        country=country_name,
    )


@app.route('/peak_predictions/', methods=['GET'])
def get_peak_predictions():
    cases_data = fetch_latest_cases_data()
    covid_data = process_covid_data(
        cases_data,
        get_daily_change=True,
        get_rolling_average=True,
    )
    country_set = ['Belgium', 'Germany', 'Netherlands', 'US']
    plot_data = predict_peaks_using_gmm(
        covid_data,
        country_set=country_set,
    )
    y_axis_title = construct_y_axis_title(
        'infections',
        get_rolling_average=True,
        get_daily_change=True,
        normalise_by_population=False,
    )
    peaks_figure = plot_peaks(plot_data, y_axis_title=y_axis_title)
    peaks_figure = json.dumps(peaks_figure, cls=plotly.utils.PlotlyJSONEncoder)
    return flask.render_template(
        'index.html',
        plot=peaks_figure,
        country=', '.join(country_set),
    )
