import datetime as dt
from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.mixture import GaussianMixture


@dataclass
class GaussianMixtureData:
    """
    Holds the data associated with one component of a Gaussian mixture model
    """
    date_list: List[str]
    covid_data: np.ndarray


@dataclass
class PlottingData:
    """
    Contains the data needed to plot the peak and non-peak data as per the Gaussian
    mixture model.
    """
    full_date_list: List[str]
    full_covid_data_list: np.ndarray
    state_1_date_list: List[str]
    state_1_covid_data_list: np.ndarray
    class_0_plot_name: str
    class_1_plot_name: str


def add_gaps_for_non_consecutive_dates(
    gaussian_mixture_data: GaussianMixtureData,
) -> GaussianMixtureData:
    """
    Takes a list of dates and adds in spaces where there are gaps between the dates,
    while also adding the same spaces to the COVID data

    Parameters
    ----------
    gaussian_mixture_data
        The data for the Gaussian mixture component. This contains the list of dates
        and the COVID data values

    Returns
    -------
    GaussianMixtureData
        The dates for the Gaussian mixture component, with spaces where there were gaps
        in the dates
    """
    date_list = gaussian_mixture_data.date_list
    covid_data = gaussian_mixture_data.covid_data
    date_list_with_spaces, covid_data_with_spaces = [date_list[0]], [covid_data[0]]
    for index, (date, prev_date) in enumerate(zip(date_list[1:], date_list[:-1])):
        converted_date = dt.datetime.strptime(date, "%m/%d/%y")
        converted_prev_date = dt.datetime.strptime(prev_date, "%m/%d/%y")
        if not converted_date - dt.timedelta(1) == converted_prev_date:
            date_list_with_spaces.append('')
            covid_data_with_spaces.append('')
        date_list_with_spaces.append(date)
        covid_data_with_spaces.append(covid_data[index + 1])
    return GaussianMixtureData(date_list_with_spaces, covid_data_with_spaces)


def predict_peaks_using_gmm(
    covid_data: pd.DataFrame,
    threshold: int = 10,
    country_set: Optional[List[str]] = None,
) -> List[PlottingData]:
    """
    Predicts the peak and non-peak split for each country using a Gaussian mixture model

    Parameters
    ----------
    covid_data
        The COVID data
    threshold
        The threshold used to adjust the data. If this is 10, the data will be
        normalised relative to the 10th death/infection/recovery
    country_set
        An optional list of countries that should be displayed

    Returns
    -------
    List[PlottingData]
        A list of PlottingData objects which contain the data required to construct
        the plot for each country
    """
    plotting_data_list = []
    # Set up a GMM with 2 components - peak and non-peak
    gmm = GaussianMixture(n_components=2)

    for country in covid_data.index:
        if country_set and country not in country_set:
            continue
        country_data = covid_data.loc[country].dropna()
        first_threshold_exceeding_index = (
            pd.to_datetime(country_data[country_data >= threshold].index[0])
        )
        country_data = country_data[
            pd.to_datetime(country_data.index) >= first_threshold_exceeding_index
        ]

        if len(country_data) < 5:
            continue
        # Reshape the values into a 2D numpy array (required by the GMM models)
        covid_values = np.reshape(country_data.values, (-1, 1))
        predictions = gmm.fit_predict(covid_values)

        class_one_mean = np.mean(country_data[predictions == 1])
        class_zero_mean = np.mean(country_data[predictions == 0])
        peak = 1 if class_one_mean > class_zero_mean else 0
        class_1_plot_name = f"{country} - {'Peak' if peak == 1 else 'Off-peak'}"
        class_0_plot_name = f"{country} - {'Peak' if peak == 0 else 'Off-peak'}"

        # Process the data for plotting. To make the data change color, a scatter plot
        # with all the data is plotted and then a scatter plot with the class 1 data
        # is plotted. To ensure that the scatter plot is correct, the missing data in
        # the class 1 data need to be filled with spaces.
        component_one_data = GaussianMixtureData(
            country_data.index[predictions == 1],
            country_data[predictions == 1].values
        )
        adj_component_one_data = add_gaps_for_non_consecutive_dates(component_one_data)

        plotting_data_list.append(PlottingData(
            full_date_list=country_data.index,
            full_covid_data_list=country_data,
            state_1_date_list=adj_component_one_data.date_list,
            state_1_covid_data_list=adj_component_one_data.covid_data,
            class_1_plot_name=class_1_plot_name,
            class_0_plot_name=class_0_plot_name,
        ))
    return plotting_data_list


def plot_peaks(
    plotting_data_list: List[PlottingData],
    y_axis_title: Optional[str] = None,
) -> go.Figure:
    """
    Plots the peaks and off-peaks identified by the Gaussian mixture model. The
    countries must be plotted in order of the first date in the date list so that the
    graphs are displayed properly.

    Parameters
    ----------
    plotting_data_list
        A list of PlottingData objects which contain the data required to construct
        the plot for each country
    y_axis_title
        The title to use for the y-axis of the graph

    Returns
    -------
    go.Figure
        The figure with the peaks and off-peaks identified by the Gaussian mixture model
    """
    figure = go.Figure()
    plot_order_indices = np.argsort([
        pd.to_datetime(plot_data.full_date_list[0]) for plot_data in plotting_data_list
    ])
    plotting_data_list = [plotting_data_list[idx] for idx in list(plot_order_indices)]
    for plot_data in plotting_data_list:
        figure.add_trace(go.Scatter(
            x=plot_data.full_date_list,
            y=plot_data.full_covid_data_list,
            name=plot_data.class_0_plot_name,
            mode='lines',
            connectgaps=False,
        ))
        figure.add_trace(go.Scatter(
            x=plot_data.state_1_date_list,
            y=plot_data.state_1_covid_data_list,
            name=plot_data.class_1_plot_name,
            connectgaps=False,
            mode='lines'
        ))
    figure.update_layout(
        title=f'Predictions of the peaks in various countries<br>{y_axis_title}',
    )

    return figure
