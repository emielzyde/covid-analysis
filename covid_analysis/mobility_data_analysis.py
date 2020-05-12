import pandas as pd


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
