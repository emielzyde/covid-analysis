from functools import lru_cache

from flask_wtf import FlaskForm
from wtforms import RadioField, SelectField, SubmitField, SelectMultipleField

from covid_analysis.data_utils import fetch_latest_cases_data, preprocess_covid_data

YES_NO_CHOICES = [('Yes', 'Yes'), ('No', 'No')]


@lru_cache(maxsize=1)
def get_available_countries():
    covid_data = fetch_latest_cases_data()
    covid_data = preprocess_covid_data(covid_data)
    return list(covid_data.index)


class CountrySelectionForm(FlaskForm):
    countries = get_available_countries()
    country_choices = [tuple([country, country]) for country in countries]
    country = SelectField('Country', choices=country_choices)
    analysis_type = RadioField(
        'Type of analysis',
        choices=[
            ('cases', 'Deaths, infections and recoveries'),
            ('mobility', 'Mobility and government response data'),
        ],
        default='cases'
    )
    submit = SubmitField('Submit selection!')


class CountryDataFormatForm(FlaskForm):
    daily_changes = RadioField('Daily changes', choices=YES_NO_CHOICES, default='Yes')
    rolling_average = RadioField(
        'Rolling average',
        choices=YES_NO_CHOICES,
        default='Yes',
    )
    population_normaliser = RadioField(
        'Normalize by population',
        choices=YES_NO_CHOICES,
        default='Yes'
    )
    submit = SubmitField('Submit selection!')


class PeakPredictionSelectionForm(CountryDataFormatForm):
    available_countries = get_available_countries()
    country_choices = [tuple([country, country]) for country in available_countries]
    countries = SelectMultipleField('Countries to plot', choices=country_choices)


class MultipleCountryDataForm(CountryDataFormatForm):
    adjust_for_time_diff = RadioField(
        'Adjust for time differences',
        choices=YES_NO_CHOICES,
        default='Yes',
    )
    types_of_data = [
        ('infections', 'Infections'),
        ('deaths', 'Deaths'),
        ('recoveries', 'Recoveries'),
        ('active cases', 'Active cases'),
        ('tests', 'Tests'),
    ]
    data_type = RadioField(
        'Type of data',
        choices=types_of_data,
        default='infections',
    )
