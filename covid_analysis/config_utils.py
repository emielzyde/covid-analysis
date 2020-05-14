from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ProcessingConfigHolder:
    """
    A class holding the config used to process the COVID data, namely:

    covid_data_type
        Whether the data relates to deaths, recoveries or infections
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
    threshold
        The (optional) threshold used to adjust the data. If this is 10, the data will
        be normalised relative to the 10th death/infection/recovery
    country_set
        An optional list of countries that should be displayed
    """
    covid_data_type: str = 'infections'
    get_daily_change: bool = True
    get_rolling_average: bool = True
    normalise_by_population: bool = True
    num_rolling_average_days: int = 7
    num_presort_countries: Optional[int] = None
    threshold: Optional[int] = None
    country_set: Optional[List[str]] = None
