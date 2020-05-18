# COVID Data Analysis 

In this project, I bring together and analyse various sources of COVID data. 
The data which is displayed in the API is mainly data which I found personally useful 
when monitoring COVID-19. I also used this project as an opportunity to learn more about 
Flask. 

### API

The API is designed as follows:
1. `/` - the starting page for the app, which his redirects to several other pages, 
depending on the selections made by the user
2. `/countries/<country_name>` - display all the data (deaths, infections, 
recoveries and active cases) for a given country
3. `/peak_predictions/` - gets the predictions of the peaks (which are predicted using a
Gaussian mixture model) in various countries
4. `/cross_country_comparisons/` - used to compare COVID data across various countries
5. `/mobility_and_government_data/<country_name>` -  gets the mobility and 
government data for a given country. The mobility data shows how trends in mobility have
changed since the start of COVID. The government data shows how stringent the 
government measures in force are. Comparing these datasets also shows whether people are
following the lockdown restrictions
6. `/weekend_effect_data/<country_name>` - gets the weekend effect data for a given 
country. This can be used to analyse the extend to which data is under-reported during
weekends

The code also allows the user to select various features about the data to be displayed.
For example, users can choose to have the data normalised by the population and can
choose to see rolling averages or daily changes. For the `/peak_predictions/` page, 
the countries for which to predict the peaks can also be selected.

### Data sources 

Various data sources were used in this project. These are:
1. Data on cases, recoveries and deaths provided by Johns Hopkins University 
(https://github.com/CSSEGISandData/COVID-19)
2. Data on the number of tests performed from 'Our World in Data' 
(https://ourworldindata.org/coronavirus-testing)
3. Data on community mobility from Google (https://www.google.com/covid19/mobility/)
4. Data on government responses to the current crisis from Oxford 
(https://github.com/OxCGRT/covid-policy-tracker/)
