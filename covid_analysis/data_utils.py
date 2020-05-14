from dataclasses import dataclass
from functools import lru_cache
from typing import Union

import pandas as pd

country_name_mapper = {
    'United States': 'US',
    'Russian Federation': 'Russia',
    'Korea, Dem. People’s Rep.': 'Korea, South',
    'Iran, Islamic Rep.': 'Iran',
    'Czech Republic': 'Czechia',
    'Egypt, Arab Rep.': 'Egypt',
    'Brunei Darussalam': 'Brunei',
    'Congo, Rep.': 'Congo (Brazzaville)',
    'Congo, Dem. Rep.': 'Congo (Kinshasa)',
    'Kyrgyz Republic': 'Kyrgyzstan',
    'Venezuela, RB': 'Venezuela',
    'Slovak Republic': 'Slovakia',
    'Syrian Arab Republic': 'Syria',
    'Lao PDR': 'Laos',
    'Yemen, Rep.': 'Yemen',
    'Myanmar': 'Burma',
}

data_to_drop = [
    'Diamond Princess',
    'Holy See',
    'Taiwan*',
    'MS Zaandam',
    'Western Sahara',
]


@lru_cache(maxsize=1)
def fetch_latest_cases_data():
    return pd.read_csv(
        'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19'
        '_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
    )


@lru_cache(maxsize=1)
def fetch_latest_deaths_data():
    return pd.read_csv(
        'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19'
        '_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'
    )


@lru_cache(maxsize=1)
def fetch_latest_recovered_data():
    return pd.read_csv(
        'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19'
        '_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv',
    )


def preprocess_covid_data(data: pd.DataFrame) -> pd.DataFrame:
    """
    Processes the COVID data by removing unnecessary columns, grouping the data by
    country and removing some non-country data (e.g. data for cruise ships)

    Parameters
    ----------
    data
        The COVID data to process

    Returns
    -------
    pd.DataFrame
        The processed COVID data
    """
    required_cols = [col for col in data.columns if col not in ['Lat', 'Long']]
    grouped_data = data.groupby('Country/Region')[required_cols].sum()
    grouped_data = grouped_data[~grouped_data.index.isin(data_to_drop)]
    return grouped_data


@dataclass
class LatestCovidData:
    """
    A class holding the latest COVID cases, deaths and recoveries data
    """
    cases_data: pd.DataFrame = preprocess_covid_data(fetch_latest_cases_data())
    deaths_data: pd.DataFrame = preprocess_covid_data(fetch_latest_deaths_data())
    recovered_data: pd.DataFrame = preprocess_covid_data(fetch_latest_recovered_data())
    active_data: pd.DataFrame = cases_data - (deaths_data + recovered_data)


@lru_cache(maxsize=1)
def fetch_population_data() -> pd.DataFrame:
    """
    Reads and processes the World Bank population data. Processing the data involves
    adjusting the names of some countries which differ between the World Bank data and
    the JHU CSSE data (e.g. US vs. United States). The data is also converted to
    millions and only the most recent data (2018) is extracted.

    Returns
    -------
    pd.DataFrame
        The processed World Bank population data
    """
    population_data = pd.read_csv(
        '/Users/emielzyde/Downloads/API_SP/API_SP.POP.TOTL_DS2_en_csv_v2_988606.csv'
    )

    # Apply processing to the country names
    population_data['Country Name'] = population_data['Country Name'].apply(
        lambda x: x.split(',')[0]
        if len(x.split(',')) > 1 and x.split(',')[1] == ' The' else x
    )
    population_data['Country Name'] = population_data['Country Name'].apply(
        lambda x: x.replace('St.', 'Saint') if 'St.' in x else x
    )
    population_data['Country Name'] = (
        population_data['Country Name']
        .
        apply(lambda country_name: country_name_mapper.get(country_name, country_name))
    )
    # Get the latest data (2018) and convert to millions
    population_data = population_data[['Country Name', '2018']]
    population_data['2018'] /= 1000000
    return population_data


def extract_matching_population_data(
    covid_data: Union[pd.DataFrame, pd.Series],
) -> Union[pd.DataFrame, pd.Series]:
    """
    Filters the population data so that it only includes the data for countries which
    are present in the COVID data

    Parameters
    ----------
    covid_data
        The COVID data

    Returns
    -------
    Union[pd.DataFrame, pd.Series]
        The filtered population data
    """
    population_data = fetch_population_data()
    if isinstance(covid_data, pd.Series):
        return (
            population_data[
                population_data['Country Name'] == covid_data.name
            ]['2018']
            .values[0]
        )

    population_data = (
        population_data[population_data['Country Name'].isin(covid_data.index.unique())]
    )
    population_data = population_data.set_index('Country Name')
    return population_data
