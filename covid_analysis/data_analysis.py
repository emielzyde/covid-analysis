from typing import List, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .data_utils import (
    preprocess_covid_data,
    extract_matching_population_data,
)


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


def plot_data_per_country(data: pd.DataFrame, num_countries: int):
    """
    Plots the COVID data for each country

    Parameters
    ----------
    data
        The processed COVID data
    num_countries
        The number of countries for which the data should be plotted
    """
    figure = go.Figure()
    for country in data.index[:num_countries]:
        figure.add_trace(go.Scatter(
            x=list(data.columns),
            y=data.loc[country],
            name=country,
        ))
    figure.show()


def calculate_daily_changes(data: pd.DataFrame) -> pd.DataFrame:
    """
    Converts the absolute values in a dataframe to daily changes

    Parameters
    ----------
    data
        The dataframe whose values should be converted to daily changes. The indices
        should be countries and the values should be the figures over time.

    Returns
    -------
    pd.DataFrame
        The dataframe with the values converted to daily changes
    """
    return data - data.shift(1, axis=1)


def calculate_rolling_average(
    data: pd.DataFrame,
    num_days: Optional[int] = 7,
) -> pd.DataFrame:
    """
    Calculates a rolling average from the data

    Parameters
    ----------
    data
        The dataframe whose values should be converted to a rolling average
    num_days
        The number of days to use in the rolling average

    Returns
    -------
    pd.DataFrame
        The dataframe with the values converted to rolling averages
    """
    return data.rolling(num_days, axis=1).mean()


def process_covid_data(
    covid_data: pd.DataFrame,
    get_daily_change: bool = True,
    get_rolling_average: bool = True,
    normalise_by_population: bool = True,
    num_rolling_average_days: int = 7,
    num_presort_countries: Optional[int] = None,
):
    """
    Processes and plots the COVID data 
    
    Parameters
    ----------
    covid_data
        The COVID data. This can be the number of cases, deaths or recoveries over time
        per country
    get_daily_change
        Whether to convert the data to daily changes (rather than total figures)
    get_rolling_average
        Whether to get a rolling average (which smooths out the data)
    normalise_by_population
        Whether to normalise the data per country by the population count
    num_rolling_average_days
        The number of days for which the rolling average should be calculated
    num_presort_countries
        If this argument is given, the data will be pre-sorted before normalising the
        data by the population count. This avoids the distortion of the data by smaller
        countries.
    """
    covid_data = preprocess_covid_data(covid_data)

    if get_daily_change:
        covid_data = calculate_daily_changes(covid_data)
    if get_rolling_average:
        covid_data = calculate_rolling_average(covid_data, num_rolling_average_days)
    if num_presort_countries:
        covid_data = sort_data_ascending(covid_data)[:num_presort_countries]

    if normalise_by_population:
        population_data = extract_matching_population_data(covid_data)
        covid_data = normalise_by_population_count(covid_data, population_data)
    covid_data = sort_data_ascending(covid_data)
    return covid_data


def adjust_for_time_differences(
    covid_data: pd.DataFrame,
    threshold: int,
    get_daily_change: bool = True,
    get_rolling_average: bool = True,
    normalise_by_population: bool = True,
    num_presort_countries: int = 20,
    num_rolling_average_days: int = 7,
    country_set: Optional[List[str]] = None,
):
    """
    Adjusts the COVID data for time differences between countries. For example, the data
    may be specified relative to the 10th infection in each country. This enables easier
    comparisons between countries without having a distortion due to differences in the
    timing of the virus spread.

    Parameters
    ----------
    covid_data
        The COVID data
    threshold
        The threshold used to adjust the data. If this is 10, the data will be
        normalised relative to the 10th death/infection/recovery
    get_daily_change
        Whether to convert the data to daily changes (rather than total figures)
    get_rolling_average
        Whether to get a rolling average (which smooths out the data)
    normalise_by_population
        Whether to normalise the data per country by the population count
    num_presort_countries
        If this argument is given, the data will be pre-sorted before normalising the
        data by the population count. This avoids the distortion of the data by smaller
        countries.
    num_rolling_average_days
        The number of days for which the rolling average should be calculated
    country_set
        An optional list of countries that should be displayed
    """
    covid_data = preprocess_covid_data(covid_data)

    if get_daily_change:
        covid_data = calculate_daily_changes(covid_data)
    if get_rolling_average:
        covid_data = calculate_rolling_average(covid_data, num_rolling_average_days)
    if num_presort_countries:
        covid_data = sort_data_ascending(covid_data)[:num_presort_countries]

    adjusted_data = covid_data[covid_data > threshold]
    if normalise_by_population:
        population_data = extract_matching_population_data(adjusted_data)
        adjusted_data = normalise_by_population_count(adjusted_data, population_data)
    if country_set:
        adjusted_data = adjusted_data[adjusted_data.index.isin(country_set)]
    if num_presort_countries:
        adjusted_data = sort_data_ascending(adjusted_data)[:num_presort_countries]

    # Plot the data
    figure = go.Figure()
    for country in adjusted_data.index:
        country_data = adjusted_data.loc[country].dropna()
        figure.add_trace(go.Scatter(
            x=list(range(len(country_data.index))),
            y=country_data,
            name=country,
        ))
    figure.show()
