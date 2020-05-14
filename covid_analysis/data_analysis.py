
from typing import Optional, Union

import inflect
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .config_utils import ProcessingConfigHolder
from .data_utils import (
    extract_matching_population_data,
    LatestCovidData,
)
from .plotting_utils import construct_y_axis_title

inflect_engine = inflect.engine()


def normalise_by_population_count(
    covid_data: pd.DataFrame,
    population_data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Normalises the COVID data by dividing the figures by the population data (where
    the population data is expressed in millions of people)

    Parameters
    ----------
    covid_data
        The COVID data
    population_data
        The population data (extracted from the World Bank)

    Returns
    -------
    pd.DataFrame
        The COVID data normalised by the population data
    """
    normalised_data = covid_data.copy()
    for country in covid_data.index:
        if country in population_data.index:
            normalised_data.loc[country] = (
                covid_data.loc[country] / population_data.loc[country].values
            )
        else:
            normalised_data.loc[country] = np.nan
    return normalised_data


def sort_data_ascending(data: pd.DataFrame) -> pd.DataFrame:
    """
    Sorts the data in ascending order based on the last column (the most recent data)

    Parameters
    ----------
    data
        The data to sort

    Returns
    -------
    pd.DataFrame
        The sorted data
    """
    return data.sort_values(data.columns[-1], ascending=False)


def plot_data_per_country(
    data: pd.DataFrame,
    processing_config: ProcessingConfigHolder,
    num_countries: int = 200,
) -> go.Figure:
    """
    Gets a plot of the COVID data

    Parameters
    ----------
    data
        The processed COVID data
    num_countries
        The number of countries for which the data should be plotted
    processing_config
        A dataclass which holds the config for processing the data

    Returns
    -------
    go.Figure
        A plot of the COVID data
    """
    figure = go.Figure()
    for country in data.index[:num_countries]:
        country_data = data.loc[country].dropna()
        x_values = (
            list(range(len(country_data.index)))
            if processing_config.threshold else list(country_data.index)
        )
        figure.add_trace(go.Scatter(
            x=x_values,
            y=country_data,
            name=country,
        ))
    y_axis_title = construct_y_axis_title(
        processing_config.covid_data_type,
        processing_config,
    )
    if processing_config.threshold:
        singular_covid_data_type = inflect_engine.singular_noun(
            processing_config.covid_data_type,
        )
        x_axis_text = (
            f'Days since {processing_config.threshold}th {singular_covid_data_type}'
        )
        figure.update_xaxes(title={'text': x_axis_text})
    figure.update_layout(title={'text': y_axis_title})
    return figure


def calculate_daily_changes(
    data: Union[pd.DataFrame, pd.Series],
) -> Union[pd.DataFrame, pd.Series]:
    """
    Converts the absolute values in a dataframe to daily changes

    Parameters
    ----------
    data
        The dataframe or series whose values should be converted to daily changes.
        The indices should be countries and the values should be the figures over time.

    Returns
    -------
    Union[pd.DataFrame, pd.Series]
        The dataframe or series with the values converted to daily changes
    """
    axis = 1 if isinstance(data, pd.DataFrame) else 0
    return data - data.shift(1, axis=axis)


def calculate_rolling_average(
    data: Union[pd.DataFrame, pd.Series],
    num_days: Optional[int] = 7,
) -> Union[pd.DataFrame, pd.Series]:
    """
    Calculates a rolling average from the data

    Parameters
    ----------
    data
        The dataframe or series whose values should be converted to a rolling average
    num_days
        The number of days to use in the rolling average

    Returns
    -------
    Union[pd.DataFrame, pd.Series]
        The dataframe or series with the values converted to rolling averages
    """
    axis = 1 if isinstance(data, pd.DataFrame) else 0
    return data.rolling(num_days, axis=axis).mean()


def process_covid_data(
    covid_data: pd.DataFrame,
    processing_config: ProcessingConfigHolder,
):
    """
    Processes and plots the COVID data 
    
    Parameters
    ----------
    covid_data
        The COVID data. This can be the number of cases, deaths or recoveries over time
        per country
    processing_config
        A dataclass which holds the config for processing the data
    """
    if processing_config.threshold:
        covid_data = covid_data[covid_data >= processing_config.threshold]
    if processing_config.get_daily_change:
        covid_data = calculate_daily_changes(covid_data)
    if processing_config.get_rolling_average:
        covid_data = calculate_rolling_average(
            covid_data,
            processing_config.num_rolling_average_days,
        )
    if processing_config.num_presort_countries:
        covid_data = (
            sort_data_ascending(covid_data)[:processing_config.num_presort_countries]
        )
    if processing_config.normalise_by_population:
        population_data = extract_matching_population_data(covid_data)
        covid_data = normalise_by_population_count(covid_data, population_data)
    if processing_config.country_set:
        covid_data = covid_data[covid_data.index.isin(processing_config.country_set)]
    covid_data = sort_data_ascending(covid_data)
    return covid_data


def get_country_data(
    covid_data: LatestCovidData,
    country_name: str,
    processing_config: ProcessingConfigHolder,
) -> go.Figure:
    """
    Gets the COVID data for a particular country

    Parameters
    ----------
    covid_data
        A dataclass holding the latest COVID data
    country_name
        The name of the country for which to return the COVID data
    processing_config
        A dataclass which holds the config for processing the data

    Returns
    -------
    go.Figure
        A plotly graph of the data for the country
    """
    deaths_data = process_covid_data(
        covid_data.deaths_data,
        processing_config,
    )
    cases_data = process_covid_data(
        covid_data.cases_data,
        processing_config,
    )
    recovered_data = process_covid_data(
        covid_data.recovered_data,
        processing_config,
    )

    figure = go.Figure()
    data_labels = ['Deaths', 'Cases', 'Recoveries']
    covid_datasets = [deaths_data, cases_data, recovered_data]
    for covid_data, label in zip(covid_datasets, data_labels):
        country_data = covid_data.loc[country_name].dropna()
        figure.add_trace(go.Scatter(
            x=list(country_data.index),
            y=country_data,
            name=label,
        ))
    y_axis_title = construct_y_axis_title(
        'deaths, infections and cases',
        processing_config,
    )
    figure.update_layout(title={'text': y_axis_title})
    return figure
