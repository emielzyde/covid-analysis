import datetime as dt

import pandas as pd

TESTING_VAR = 'total_tests'


def process_mobility_data(mobility_data_file_path: str) -> pd.DataFrame:
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
        mobility_data['variable']
        .apply(lambda x: x.replace('_percent_change_from_baseline', ''))
    )
    mobility_data = (
        mobility_data
        .set_index(['country_region', 'variable', 'date'])['value']
        .unstack()
    )
    return mobility_data


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
    government_data['Date'] = (
        government_data['Date']
        .apply(pd.to_datetime, format='%Y%m%d')
    )
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


def get_testing_data():
    """
    Loads the testing data from 'Our World in Data'. Any missing dates in the data are
    filled by using the last available figure

    Returns
    -------
    pd.DataFrame
        The processed testing data
    """
    testing_data = pd.read_csv(
        'https://covid.ourworldindata.org/data/owid-covid-data.csv'
    )
    testing_data = testing_data[['location', 'date', TESTING_VAR]]
    testing_data = testing_data.melt(
        id_vars=['location', 'date'],
        value_vars=TESTING_VAR,
    )
    testing_data = testing_data.set_index(['location', 'date', 'variable'])['value']
    testing_data = testing_data.unstack(level=1).droplevel(-1)
    testing_data = testing_data.dropna(axis=0, how='all')
    testing_data.columns = [
        dt.datetime.strptime(date, '%Y-%m-%d').strftime('%-m/%-d/%y')
        for date in testing_data.columns
    ]
    testing_data = testing_data.fillna(method='ffill', axis=1)
    return testing_data
