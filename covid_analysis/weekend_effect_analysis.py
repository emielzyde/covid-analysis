import pandas as pd
import plotly.graph_objects as go

from covid_analysis.config_utils import ProcessingConfigHolder
from covid_analysis.data_analysis import process_covid_data

WEEKDAYS = [
    'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'
]


def analyse_weekend_effects(covid_data: pd.DataFrame) -> pd.DataFrame:
    """
    Analyses the weekend effects from the COVID data

    Parameters
    ----------
    covid_data
        A dataframe holding the COVID data

    Returns
    -------
    pd.DataFrame
        A dataframe where the indices are the countries and the rows are the difference
        between the percentage of, e.g., deaths reported on each day and the percentage
        of deaths that would be expected if they were spread uniformly across the week
    """
    processing_config = ProcessingConfigHolder()
    processing_config.get_rolling_average = False
    processing_config.normalise_by_population = False
    covid_data = process_covid_data(covid_data, processing_config)

    # Covert the column names from dates to the weekdays they represent
    covid_data.columns = [
        col.day_name()
        for col in pd.to_datetime(covid_data.columns)
    ]
    daily_data_list = []
    for day in WEEKDAYS:
        daily_data = covid_data.loc[:, covid_data.columns == day].sum(axis=1)
        daily_data_list.append(daily_data)
    summed_data = pd.concat(daily_data_list, axis=1)
    summed_data.columns = WEEKDAYS
    normalised_data = summed_data.divide(
        summed_data.sum(axis=1),
        axis=0,
    )
    uniform_series = pd.Series([1/7] * 7)
    uniform_series.index = WEEKDAYS
    weekend_effect_data = (
        normalised_data
        .subtract(uniform_series, axis=1) * 100
    )
    return weekend_effect_data


def plot_weekend_effect_data(
    weekend_effect_data: pd.DataFrame,
    country: str,
    covid_data_type: str
) -> go.Figure:
    """
    Plots the weekend effect data for a given country

    Parameters
    ----------
    weekend_effect_data
        A dataframe where the indices are the countries and the rows are the difference
        between the percentage of, e.g., deaths reported on each day and the percentage
        of deaths that would be expected if they were spread uniformly across the week
    country
        The country for which to plot the data
    covid_data_type
        The type of COVID data (e.g. deaths)

    Returns
    -------
    go.Figure
        A figure showing the weekend effect data for the selected country
    """
    country_data = weekend_effect_data[weekend_effect_data.index == country]
    country_data = country_data.T.squeeze()
    figure = go.Figure()
    figure.add_trace(go.Bar(
        x=country_data.index,
        y=country_data.values,
        name='Government stringency'
    ))
    title_text = (
        f'Differences between actual and expected percentage of {covid_data_type} '
        f'(under a uniform distribution) for {country}'
    )
    figure.update_layout(title={'text': title_text})
    return figure
