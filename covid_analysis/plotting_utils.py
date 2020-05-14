from .config_utils import ProcessingConfigHolder


def construct_y_axis_title(
    covid_data_type: str,
    processing_config: ProcessingConfigHolder,
) -> str:
    """
    Construct the title for the plots

    Parameters
    ----------
    covid_data_type
        Whether the data relates to deaths, recoveries or infections
    processing_config
        A dataclass which holds the config for processing the data

    Returns
    -------
    str
        The y-axis title for the plot 
    """
    title_string_list = []
    if processing_config.get_daily_change:
        title_string_list.append('Daily ')
    else:
        title_string_list.append('Total ')
    title_string_list.append(covid_data_type)

    if processing_config.normalise_by_population:
        title_string_list.append(' per million people')
    if processing_config.get_rolling_average:
        title_string_list.append(
            f' (as a {processing_config.num_rolling_average_days} day rolling average)'
        )
    return ''.join(title_string_list)
