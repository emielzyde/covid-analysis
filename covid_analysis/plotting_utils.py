from typing import Optional


def construct_y_axis_title(
    covid_data_type: str,
    get_daily_change: bool,
    get_rolling_average: bool,
    normalise_by_population: bool,
    num_rolling_average_days: Optional[int] = 7,
) -> str:
    """
    Construct the title for the plots

    Parameters
    ----------
    covid_data_type
        Whether the data relates to deaths, recoveries or infections
    get_daily_change
        Whether the data was converted to daily changes (rather than total figures)
    get_rolling_average
        Whether the rolling average was calculated
    normalise_by_population
        Whether the data was normalised by population count
    num_rolling_average_days
        The number of days for which the rolling average should be calculated

    Returns
    -------
    Tuple[str, str]
    """
    title_string_list = []
    if get_daily_change:
        title_string_list.append('Daily ')
    else:
        title_string_list.append('Total ')
    title_string_list.append(covid_data_type)

    if normalise_by_population:
        title_string_list.append(' per million people')
    if get_rolling_average:
        title_string_list.append(
            f' (as a {num_rolling_average_days} day rolling average)'
        )
    return ''.join(title_string_list)
