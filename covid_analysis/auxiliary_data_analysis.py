import datetime as dt
from functools import lru_cache

import pandas as pd
import plotly.graph_objects as go

from .data_utils import country_name_mapper


@lru_cache(maxsize=1)
def get_mobility_data(mobility_data_file_path: str) -> pd.DataFrame:
    """
    Performs pre-processing on the COVID mobility data from Google

    Parameters
    ----------
    mobility_data_file_path
        The file path for the mobility data

    Returns
    -------
    pd.DataFrame
        The processed COVID mobility data
    """
    mobility_data = pd.read_csv(mobility_data_file_path)
    mobility_data['country_region'] = (
        mobility_data['country_region']
        .apply(lambda country_name: country_name_mapper.get(country_name, country_name))
    )
    mobility_data = mobility_data[pd.isna(mobility_data['sub_region_1'])]
    mobility_data = mobility_data.drop(
        ['sub_region_1', 'sub_region_2', 'country_region_code'],
        axis=1,
    )
    percent_change_cols = [
        col for col in mobility_data.columns if 'percent_change' in col
    ]
    mobility_data = mobility_data.melt(
        id_vars=['country_region', 'date'],
        value_vars=percent_change_cols,
    )
    mobility_data['variable'] = (
        mobility_data['variable'].apply(
            lambda x: (
                x.replace('_percent_change_from_baseline', '')
                .replace('_', ' ')
                .capitalize()
            )
        )
    )
    mobility_data = (
        mobility_data
        .set_index(['country_region', 'variable', 'date'])['value']
        .unstack()
    )
    mobility_data.columns = [
        dt.datetime.strptime(date, '%Y-%m-%d').strftime('%-m/%-d/%y')
        for date in mobility_data.columns
    ]
    return mobility_data


@lru_cache(maxsize=1)
def get_government_response_data() -> pd.DataFrame:
    """
    Loads the government response data from Oxford. This data contains information
    regarding the measures taken by governments regarding COVID, such as lockdowns
    and economic measures.

    Returns
    -------
    pd.DataFrame
        The processed government response data
    """
    government_data = pd.read_csv(
        'https://raw.githubusercontent.com/OxCGRT/covid-policy-tracker/master/data/'
        'OxCGRT_latest.csv'
    )
    government_data['CountryName'] = (
        government_data['CountryName']
        .apply(lambda country_name: country_name_mapper.get(country_name, country_name))
    )
    government_data['Date'] = (
        government_data['Date']
        .apply(pd.to_datetime, format='%Y%m%d')
    )
    government_data['Date'] = [
        date.strftime('%-m/%-d/%y')
        for date in government_data['Date']
    ]
    cols = [
        col for col in government_data.columns
        if col not in ['CountryName', 'CountryCode', 'Date']
    ]
    government_data = (
        government_data
        .melt(id_vars=['CountryName', 'Date'], value_vars=cols)
        .set_index(['CountryName', 'Date', 'variable'])['value']
    )
    return government_data


class AuxiliaryDataHolder:
    """
    A class which holds auxiliary data relating to COVID, in particular:

    government_response_data
        This Oxford data contains information regarding the measures taken by
        governments regarding COVID
    mobility_data
        The COVID mobility data from Google
    """
    government_response_data = get_government_response_data()
    mobility_data = get_mobility_data(
        'https://www.gstatic.com/covid19/mobility/Global_Mobility_Report.csv?'
        'cachebust=57b4ac4fc40528e2'
    )


def process_stringency_data(
    auxiliary_data_holder: AuxiliaryDataHolder,
    country: str,
    num_rolling_average_days: int,
) -> pd.DataFrame:
    """
    Extracts the government stringency data for a given country from the government
    response data

    Parameters
    ----------
    auxiliary_data_holder
        A dataclass holding the government data
    country
        The country for which the stringency data should be extracted
    num_rolling_average_days
        The number of days for which the rolling average should be calculated

    Returns
    -------
    pd.DataFrame
        A dataframe containing the processed stringency data for the country
    """
    government_data = auxiliary_data_holder.government_response_data
    stringency_data = (
        government_data[government_data.index.get_level_values(-1) == 'StringencyIndex']
        .droplevel(-1)
        .unstack()
    )
    stringency_data = stringency_data.reindex(
        sorted(stringency_data.columns, key=pd.to_datetime),
        axis=1,
    )
    stringency_data = stringency_data.fillna(method='ffill', axis=1)
    country_stringency_data = stringency_data[stringency_data.index == country]
    country_stringency_data = (
        country_stringency_data
        .rolling(num_rolling_average_days, axis=1)
        .mean()
        .T.squeeze()
        .dropna(axis=0, how='all')
    )
    return country_stringency_data


def process_mobility_data(
    auxiliary_data_holder: AuxiliaryDataHolder,
    country: str,
    num_rolling_average_days: int,
) -> pd.DataFrame:
    """
    Extracts the mobility for a given country from the Google data and processes the
    data

    Parameters
    ----------
    auxiliary_data_holder
        A dataclass holding the mobility data
    country
        The country for which the mobility should be extracted
    num_rolling_average_days
        The number of days for which the rolling average should be calculated

    Returns
    -------
    pd.DataFrame
        A dataframe containing the processed mobility data for the country
    """
    mobility_data = auxiliary_data_holder.mobility_data
    country_mobility_data = mobility_data[
        mobility_data.index.get_level_values(0) == country
    ]
    country_mobility_data = (
        country_mobility_data
        .rolling(num_rolling_average_days, axis=1)
        .mean()
        .dropna(axis=1, how='all')
    )
    return country_mobility_data


def plot_mobility_and_government_data(
    auxiliary_data_holder: AuxiliaryDataHolder,
    country: str,
    num_rolling_average_days: int = 4,
) -> go.Figure:
    """
    Constructs the plot for the government and mobility data for a given country

    Parameters
    ----------
    auxiliary_data_holder
        A dataclass holding the auxiliary data
    country
        The country for which the mobility should be extracted
    num_rolling_average_days
        The number of days for which the rolling average should be calculated

    Returns
    -------
    go.Figure
        A Plotly figure containing the relevant government and mobility data
    """
    country_stringency_data = process_stringency_data(
        auxiliary_data_holder,
        country,
        num_rolling_average_days,
    )
    country_mobility_data = process_mobility_data(
        auxiliary_data_holder,
        country,
        num_rolling_average_days,
    )

    first_mobility_data_date = pd.to_datetime(country_mobility_data.columns[0])
    last_mobility_data_date = pd.to_datetime(country_mobility_data.columns[-1])
    stringency_index = pd.to_datetime(country_stringency_data.index)
    country_stringency_data = country_stringency_data[
        (stringency_index >= first_mobility_data_date) &
        (stringency_index <= last_mobility_data_date)
    ]

    figure = go.Figure()
    figure.add_trace(go.Scatter(
        x=country_stringency_data.index,
        y=country_stringency_data.values,
        name='Government stringency'
    ))
    for idx, row in country_mobility_data.iterrows():
        figure.add_trace(go.Scatter(
            x=row.index,
            y=row.values,
            name=idx[1],
        ))
    title_text = (
        f'Mobility and government response data for {country} '
        f'({num_rolling_average_days} day rolling average)'
    )
    figure.update_layout(title={'text': title_text})
    return figure
