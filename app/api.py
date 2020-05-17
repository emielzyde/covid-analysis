import json

import flask
import plotly
from flask_socketio import SocketIO

from covid_analysis.auxiliary_data_analysis import (
    AuxiliaryDataHolder,
    plot_mobility_and_government_data,
)
from covid_analysis.config_utils import ProcessingConfigHolder
from covid_analysis.data_analysis import (
    get_country_data,
    process_covid_data,
    plot_data_per_country,
)
from covid_analysis.data_utils import LatestCovidData
from covid_analysis.gmm_modelling import predict_peaks_using_gmm, plot_peaks
from covid_analysis.plotting_utils import construct_y_axis_title
from covid_analysis.weekend_effect_analysis import (
    analyse_weekend_effects,
    plot_weekend_effect_data,
)
from .forms import (
    CountrySelectionForm,
    PeakPredictionSelectionForm,
    CountryDataFormatForm,
    MultipleCountryDataForm,
)

app = flask.Flask(__name__)
socketio = SocketIO(app)

LATEST_COVID_DATA = LatestCovidData()
BASE_PROCESSING_CONFIG = ProcessingConfigHolder()
RESPONSE_MAP = {'No': False, 'Yes': True}
COVID_DATA_MAP = {
    'infections': LATEST_COVID_DATA.cases_data,
    'deaths': LATEST_COVID_DATA.deaths_data,
    'recoveries': LATEST_COVID_DATA.recovered_data,
    'active cases': LATEST_COVID_DATA.active_data,
    'tests': LATEST_COVID_DATA.testing_data
}
AUXILIARY_DATA = AuxiliaryDataHolder()


@app.route('/', methods=['GET', 'POST'])
def index():
    """
    The starting page for the app. This redirects to several other pages, depending
    on the selections made by the user.
    """
    form = CountrySelectionForm()
    if form.validate_on_submit():
        if form.analysis_type.data == 'mobility':
            return flask.redirect(f'/mobility_and_government_data/{form.country.data}')
        elif form.analysis_type.data == 'weekends':
            return flask.redirect(f'/weekend_effect_data/{form.country.data}')
        return flask.redirect(f'/countries/{form.country.data}')
    return flask.render_template('home_page.html', form=form)


@app.route('/countries/<string:country_name>', methods=['GET', 'POST'])
def get_single_country_data(country_name: str):
    """
    Gets all the data (deaths, infections, recoveries and active cases)
    for a given country
    """
    processing_config = ProcessingConfigHolder()
    form = CountryDataFormatForm()

    if form.validate_on_submit():
        processing_config.get_daily_change = RESPONSE_MAP[form.daily_changes.data]
        processing_config.get_rolling_average = RESPONSE_MAP[form.rolling_average.data]
        processing_config.normalise_by_population = (
            RESPONSE_MAP[form.population_normaliser.data]
        )

    country_figure = get_country_data(
        LATEST_COVID_DATA,
        country_name,
        processing_config,
    )
    country_figure = json.dumps(country_figure, cls=plotly.utils.PlotlyJSONEncoder)
    return flask.render_template(
        'country_graph_template.html',
        plot=country_figure,
        country=country_name,
        form=form,
        fields=[form.daily_changes, form.rolling_average, form.population_normaliser]
    )


@app.route('/peak_predictions/', methods=['GET', 'POST'])
def get_peak_predictions():
    """
    Gets the predictions of the peaks in various countries. Peaks are predicted using
    a GMM model
    """
    processing_config = ProcessingConfigHolder()
    processing_config.country_set = ['Belgium', 'United Kingdom', 'US']
    form = PeakPredictionSelectionForm()

    if form.validate_on_submit():
        processing_config.country_set = form.countries.data
        processing_config.get_daily_change = RESPONSE_MAP[form.daily_changes.data]
        processing_config.get_rolling_average = RESPONSE_MAP[form.rolling_average.data]
        processing_config.normalise_by_population = RESPONSE_MAP[
            form.population_normaliser.data
        ]

    covid_data = process_covid_data(LATEST_COVID_DATA.cases_data, processing_config)
    plot_data = predict_peaks_using_gmm(
        covid_data,
        country_set=processing_config.country_set,
    )
    y_axis_title = construct_y_axis_title(
        'infections',
        processing_config,
    )
    peaks_figure = plot_peaks(plot_data, y_axis_title=y_axis_title)
    peaks_figure = json.dumps(peaks_figure, cls=plotly.utils.PlotlyJSONEncoder)
    return flask.render_template(
        'graph_template.html',
        plot=peaks_figure,
        country=', '.join(processing_config.country_set),
        form=form,
        fields=[form.daily_changes, form.rolling_average, form.population_normaliser]
    )


@app.route('/cross_country_comparisons/', methods=['GET', 'POST'])
def get_country_comparisons():
    """
    Used to compare COVID data across various countries. For example, this allows for
    the comparison of deaths per million people across a range of countries (which
    can be selected by the user)
    """
    processing_config = ProcessingConfigHolder()
    processing_config.num_presort_countries = 50
    form = MultipleCountryDataForm()
    base_covid_data = LATEST_COVID_DATA.cases_data
    if form.validate_on_submit():
        processing_config.get_daily_change = RESPONSE_MAP[form.daily_changes.data]
        processing_config.get_rolling_average = RESPONSE_MAP[form.rolling_average.data]
        processing_config.normalise_by_population = RESPONSE_MAP[
            form.population_normaliser.data
        ]
        processing_config.threshold = (
            10 if form.adjust_for_time_diff.data == 'Yes' else None
        )
        processing_config.covid_data_type = form.data_type.data
        base_covid_data = COVID_DATA_MAP[form.data_type.data]

    covid_data = process_covid_data(base_covid_data, processing_config)
    covid_figure = plot_data_per_country(
        covid_data,
        processing_config,
        num_countries=10,
    )
    covid_figure = json.dumps(covid_figure, cls=plotly.utils.PlotlyJSONEncoder)
    return flask.render_template(
        'country_graph_template.html',
        plot=covid_figure,
        country='multiple countries',
        form=form,
        fields=[
            form.daily_changes,
            form.rolling_average,
            form.population_normaliser,
            form.adjust_for_time_diff,
            form.data_type,
        ]
    )


@app.route('/mobility_and_government_data/<string:country_name>', methods=['GET'])
def get_mobility_and_government_data(country_name: str):
    """
    Gets the mobility and government data for a given country. The mobility data
    shows how trends in mobility have changed since the start of COVID. The government
    data shows how stringent the government measures in force are.
    """
    mobility_figure = plot_mobility_and_government_data(AUXILIARY_DATA, country_name)
    mobility_figure = json.dumps(mobility_figure, cls=plotly.utils.PlotlyJSONEncoder)
    return flask.render_template(
        'aux_data_template.html',
        plot=mobility_figure,
        country=country_name,
    )


@app.route('/weekend_effect_data/<string:country_name>', methods=['GET'])
def get_weekend_effect_data(country_name: str):
    """
    Gets the weekend effect data for a given country. This shows the differences in
    report during (and shortly after) weekends, relative to the rest of the week.
    """
    weekend_effect_data = analyse_weekend_effects(LATEST_COVID_DATA.deaths_data)
    weekend_effect_figure = plot_weekend_effect_data(
        weekend_effect_data,
        country_name,
        'deaths',
    )
    weekend_effect_figure = json.dumps(
        weekend_effect_figure,
        cls=plotly.utils.PlotlyJSONEncoder,
    )
    return flask.render_template(
        'aux_data_template.html',
        plot=weekend_effect_figure,
        country=country_name,
    )
