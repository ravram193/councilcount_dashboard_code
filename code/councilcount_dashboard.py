# %%
# installing packages
import pandas as pd
import numpy as np
import geopandas as gpd
from copy import deepcopy
import argparse
import sys
import dash, dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc 
from dash import Output, Input, html, callback

# importing my functions 
from update_output_functions_census import create_name_to_code_dict, b64_image, folium_plot, get_table_tab1, get_table_tab2, convert_df_to_dash, make_line_chart 

# %% [markdown]
# ### Instructions for running the CouncilCount dashboard code
# 
# Now that all estimate datasets have been generated and downloaded, you are ready to launch the CouncilCount Dashboard! Most of the code in this file doesn't need to be changed when updating the dashboard with new survey years or variables. The changes that need to be made manually are as follows:
# 
# * The variable `acs_years`, which is a list, must be updated with the years that will be presented on the dashboard. Each survey should be represented by its end year (e.g. 2021 would represent the 2017-2021 ACS). Estimates for all of the years in the list must be downloaded in the data folder in order for the dashboard to run.
# * Any new variables must be added to `dropdown_dict`. 
# 
# Here is an example entry for `dropdown_dict`:
# 
# ```
# {'value': 'Lived in the same house 1 year ago', 'label': 'Same house', 'group': 'Residence 1 Year Ago'}
# ```
# 
# The 'value' entry represents the full name of variable as it is written in the `variable_code_dict` found in `004_create_variable_code_dicts.ipynb`; 'label' represents the user-facing name on the dashboard (can be shorter or more concise since there will be category headers that provide context for what the variable is refering to); and 'group' represents the name of the category that the variable belongs to (will be displayed in the dropdown menu with all other variables placed in the same category). When adding new variables to CouncilCount, be sure that they all receive a `dropdown_dict` entry that follows this structure. This dict will help build dropdown menus on the dashboard.

# %%
# years that will be added to the dashboard
# any changes to available times on the dashboard should be made here

acs_years = [2011, 2016, 2023]
acs_years = sorted(acs_years) # to ensure years are in ascending order

# convert to time periods (to be used in setting dashboard time period options)
time_periods = [str(year-4) + '-' + str(year) for year in acs_years] 

# %%
# uploading data dictionaries for each year

for year in acs_years:

    globals()[f'data_dictionary_{year}'] = pd.read_csv(f'../data/output/ACS_estimates_{year}/data_dictionary_{year}.csv')
    # creating a version with simplified description for Unemployment rate, to be used in creating name_to_code_dict
    globals()[f'data_dictionary_{year}_edited'] = deepcopy(globals()[f'data_dictionary_{year}']) 
    globals()[f'data_dictionary_{year}_edited']['estimate_description'] = globals()[f'data_dictionary_{year}_edited']['estimate_description'].replace('% Unemployment rate: DP03_0005E (unemployed) / DP03_0002E (labor force)', 'Unemployment rate')
    # creating dicts to be used in dashboard functions
    globals()[f'name_to_code_dict_{year}'] = create_name_to_code_dict(globals()[f'data_dictionary_{year}_edited'], denoms = False)
    globals()[f'name_to_denom_dict_{year}'] = create_name_to_code_dict(globals()[f'data_dictionary_{year}_edited'], denoms = True)

# %%
# adding the datasets for each year

remove_ntas = []

for year in acs_years:

    # uploading data for each geography type
    globals()[f'nyc_wide_estimates_{year}'] = pd.read_csv(f'../data/output/ACS_estimates_{year}/nyc-wide_estimates_{year}.csv').apply(lambda col: col.map(lambda x: np.nan if x is None else x))
    globals()[f'councildist_2013_geographies_{year}'] = gpd.read_file(f'../data/output/ACS_estimates_{year}/councildist_2013-geographies_{year}.geojson').apply(lambda col: col.map(lambda x: np.nan if x is None else x))
    globals()[f'councildist_2023_geographies_{year}'] = gpd.read_file(f'../data/output/ACS_estimates_{year}/councildist_2023-geographies_{year}.geojson').apply(lambda col: col.map(lambda x: np.nan if x is None else x))
    globals()[f'communitydist_geographies_{year}_all_regions'] = gpd.read_file(f'../data/output/ACS_estimates_{year}/communitydist-geographies_{year}.geojson').apply(lambda col: col.map(lambda x: np.nan if x is None else x))
    globals()[f'schooldist_geographies_{year}'] = gpd.read_file(f'../data/output/ACS_estimates_{year}/schooldist-geographies_{year}.geojson').apply(lambda col: col.map(lambda x: np.nan if x is None else x))
    globals()[f'policeprct_geographies_{year}_all_regions'] = gpd.read_file(f'../data/output/ACS_estimates_{year}/policeprct-geographies_{year}.geojson').apply(lambda col: col.map(lambda x: np.nan if x is None else x))
    globals()[f'modzcta_geographies_{year}_all_regions'] = gpd.read_file(f'../data/output/ACS_estimates_{year}/modzcta-geographies_{year}.geojson').apply(lambda col: col.map(lambda x: np.nan if x is None else x))
    globals()[f'nta_geographies_{year}_all_regions'] = gpd.read_file(f'../data/output/ACS_estimates_{year}/nta-geographies_{year}.geojson').apply(lambda col: col.map(lambda x: np.nan if x is None else x))
    globals()[f'borough_geographies_{year}'] = gpd.read_file(f'../data/output/ACS_estimates_{year}/borough-geographies_{year}.geojson').apply(lambda col: col.map(lambda x: np.nan if x is None else x))
    
    # fixing index/ columns
    
    globals()[f'nyc_wide_estimates_{year}'] = globals()[f'nyc_wide_estimates_{year}'].set_index('city')
    globals()[f'nyc_wide_estimates_{year}'] = globals()[f'nyc_wide_estimates_{year}'].rename(columns={'city_name':'city'})

    globals()[f'councildist_2013_geographies_{year}']['councildist_2013'] = globals()[f'councildist_2013_geographies_{year}']['councildist_2013'].astype(int) # ensuring that index is consistently int across all datasets
    globals()[f'councildist_2013_geographies_{year}'] = globals()[f'councildist_2013_geographies_{year}'].set_index('councildist_2013') 
    globals()[f'councildist_2013_geographies_{year}'] = globals()[f'councildist_2013_geographies_{year}'].rename(columns={'CounDist':'councildist_2013'})

    globals()[f'councildist_2023_geographies_{year}']['councildist_2023'] = globals()[f'councildist_2023_geographies_{year}']['councildist_2023'].astype(int)
    globals()[f'councildist_2023_geographies_{year}'] = globals()[f'councildist_2023_geographies_{year}'].set_index('councildist_2023')
    globals()[f'councildist_2023_geographies_{year}'] = globals()[f'councildist_2023_geographies_{year}'].rename(columns={'coun_dist':'councildist_2023'})

    globals()[f'schooldist_geographies_{year}']['schooldist'] = globals()[f'schooldist_geographies_{year}']['schooldist'].astype(int)
    globals()[f'schooldist_geographies_{year}'] = globals()[f'schooldist_geographies_{year}'].set_index('schooldist')
    globals()[f'schooldist_geographies_{year}'] = globals()[f'schooldist_geographies_{year}'].rename(columns={'school_dist':'schooldist'})

    globals()[f'modzcta_geographies_{year}_all_regions']['modzcta'] = globals()[f'modzcta_geographies_{year}_all_regions']['modzcta'].astype(int)
    globals()[f'modzcta_geographies_{year}_all_regions'] = globals()[f'modzcta_geographies_{year}_all_regions'].set_index('modzcta').sort_index()
    globals()[f'modzcta_geographies_{year}_all_regions'] = globals()[f'modzcta_geographies_{year}_all_regions'].rename(columns={'MODZCTA':'modzcta'})
    
    # keeping a version with all regions included for download button version
    globals()[f'modzcta_geographies_{year}'] = deepcopy(globals()[f'modzcta_geographies_{year}_all_regions'])
    # removing zip 99999 (represents parks)
    globals()[f'modzcta_geographies_{year}'] = globals()[f'modzcta_geographies_{year}'].drop(99999)

    globals()[f'communitydist_geographies_{year}_all_regions']['communitydist'] = globals()[f'communitydist_geographies_{year}_all_regions']['communitydist'].astype(int)    
    globals()[f'communitydist_geographies_{year}_all_regions'] = globals()[f'communitydist_geographies_{year}_all_regions'].set_index('communitydist')
    globals()[f'communitydist_geographies_{year}_all_regions'] = globals()[f'communitydist_geographies_{year}_all_regions'].rename(columns={'boro_cd':'communitydist'})

    # keeping a version with all regions included for download button version
    globals()[f'communitydist_geographies_{year}'] = deepcopy(globals()[f'communitydist_geographies_{year}_all_regions']) 
    # for mapping, removing regions that will not be included (joint interest areas)
    joint_interest_areas = [164, 226, 227, 228, 355, 356, 480, 481, 482, 483, 484, 595]
    globals()[f'communitydist_geographies_{year}'] = globals()[f'communitydist_geographies_{year}'].drop(joint_interest_areas)
#     globals()[f'communitydist_geographies_{year}'] = globals()[f'communitydist_geographies_{year}'][~globals()[f'communitydist_geographies_{year}'][globals()[f'name_to_code_dict_{year}']['Total population']].isnull()]

    globals()[f'policeprct_geographies_{year}_all_regions']['policeprct'] = globals()[f'policeprct_geographies_{year}_all_regions']['policeprct'].astype(int)    
    globals()[f'policeprct_geographies_{year}_all_regions'] = globals()[f'policeprct_geographies_{year}_all_regions'].set_index('policeprct')
    globals()[f'policeprct_geographies_{year}_all_regions'] = globals()[f'policeprct_geographies_{year}_all_regions'].rename(columns={'precinct':'policeprct'})

    # keeping a version with all regions included for download button version
    globals()[f'policeprct_geographies_{year}'] = deepcopy(globals()[f'policeprct_geographies_{year}_all_regions']) 
    # removing central park precinct for map
    globals()[f'policeprct_geographies_{year}'] = globals()[f'policeprct_geographies_{year}'].drop(22)
#     globals()[f'policeprct_geographies_{year}'] = globals()[f'policeprct_geographies_{year}'][~globals()[f'policeprct_geographies_{year}'][globals()[f'name_to_code_dict_{year}']['Total population']].isnull()]

    globals()[f'nta_geographies_{year}_all_regions'] = globals()[f'nta_geographies_{year}_all_regions'].set_index('nta')
    globals()[f'nta_geographies_{year}_all_regions'] = globals()[f'nta_geographies_{year}_all_regions'].rename(columns={'nta2020':'nta'})
    # finding set of NTAs that have a population under 300 in at least one year
    # these will be removed from all years for consistency
    remove_ntas = remove_ntas + globals()[f'nta_geographies_{year}_all_regions'].loc[globals()[f'nta_geographies_{year}_all_regions'][globals()[f'name_to_code_dict_{year}']['Total population: Data Profiles 5-Year']] <= 300, 'nta'].to_list()

    globals()[f'borough_geographies_{year}'] = globals()[f'borough_geographies_{year}'].set_index('borough')
    globals()[f'borough_geographies_{year}'] = globals()[f'borough_geographies_{year}'].rename(columns={'boro_name':'borough'})

    # converting to GeoDataFrames so choropleth map will read the geometry columns 
                                                                          
    globals()[f'councildist_2013_geographies_{year}'] = globals()[f'councildist_2013_geographies_{year}'].to_crs(2263)
    globals()[f'councildist_2023_geographies_{year}'] = globals()[f'councildist_2023_geographies_{year}'].to_crs(2263)
    globals()[f'policeprct_geographies_{year}'] = globals()[f'policeprct_geographies_{year}'].to_crs(2263)
    globals()[f'schooldist_geographies_{year}'] = globals()[f'schooldist_geographies_{year}'].to_crs(2263) 
    globals()[f'modzcta_geographies_{year}'] = globals()[f'modzcta_geographies_{year}'].to_crs(2263) 
    globals()[f'communitydist_geographies_{year}'] = globals()[f'communitydist_geographies_{year}'].to_crs(2263)     
    globals()[f'borough_geographies_{year}'] = globals()[f'borough_geographies_{year}'].to_crs(2263)  

# finishing up NTA dataset now that low-population areas have been collected from all years' datasets
for year in acs_years:
    
    # keeping a version with all regions included for download button version
    globals()[f'nta_geographies_{year}'] = deepcopy(globals()[f'nta_geographies_{year}_all_regions']) 
    # removing NTAs with low populations (mainly parks, cemetaries, etc.) for map
    globals()[f'nta_geographies_{year}'] = globals()[f'nta_geographies_{year}'].drop(remove_ntas)
#     globals()[f'nta_geographies_{year}'] = globals()[f'nta_geographies_{year}'][~globals()[f'nta_geographies_{year}'][globals()[f'name_to_code_dict_{year}']['Total population']].isnull()]

    globals()[f'nta_geographies_{year}'] = globals()[f'nta_geographies_{year}'].to_crs(2263)

# %%
# for converting full NTA names to shorter names in the table on tab 1 (so NTA names aren't too long)
# using acs_years[-1] to access the most recent year's NTA conversions

nta_dict = pd.Series(globals()[f'nta_geographies_{acs_years[-1]}']['nta_code'].values,index=globals()[f'nta_geographies_{acs_years[-1]}']['nta'].astype(str)).to_dict()

# %%
# dict holding all of the variables that will be displayed in the dropdown menu in the dashboard
# 'value' is the input for the callback function
# 'label' sets the displayed names in the dropdown
# 'group' creates sub-headings in the dropdown

dropdown_dict = [
    
    # there are multiple entries for total pop/ households across different surveys, so just choosing one survey to draw from
    # all values total pop/ households are the same across surveys, so specific selection doesn't matter
    {'value': 'Total population: Data Profiles 5-Year', 'label': 'Total population', 'group': 'Population'},
    {'value': 'Total households: Data Profiles 5-Year', 'label': 'Total households', 'group': 'Population'},
    
    {'value': 'Female', 'label': 'Female', 'group': 'Sex'},
    {'value': 'Male', 'label': 'Male', 'group': 'Sex'},
    
    {'value': 'Hispanic or Latino', 'label': 'Hispanic or Latino', 'group': 'Ethnicity'},
    {'value': 'Not Hispanic or Latino', 'label': 'Not Hispanic or Latino', 'group': 'Ethnicity'},
                
    {'value': 'American Indian and Alaska Native alone', 'label': 'American Indian and Alaska Native alone', 'group': 'Race'},
    {'value': 'Asian alone', 'label': 'Asian alone', 'group': 'Race'},
    {'value': 'Black or African American alone', 'label': 'Black or African American alone', 'group': 'Race'},
    {'value': 'Native Hawaiian and Other Pacific Islander alone', 'label': 'Native Hawaiian and Other Pacific Islander alone', 'group': 'Race'},
    {'value': 'White alone', 'label': 'White alone', 'group': 'Race'},
    {'value': 'Some other race alone', 'label': 'Some other race alone', 'group': 'Race'},
    {'value': 'Two or more races', 'label': 'Two or more races', 'group': 'Race'},
        
    {'value': 'American Indian and Alaska Native alone, not Hispanic or Latino', 'label': 'American Indian and Alaska Native alone, not Hispanic or Latino', 'group': 'Race and Ethnicity'},
    {'value': 'Asian alone, not Hispanic or Latino', 'label': 'Asian alone, not Hispanic or Latino', 'group': 'Race and Ethnicity'},
    {'value': 'Black or African American alone, not Hispanic or Latino', 'label': 'Black or African American alone, not Hispanic or Latino', 'group': 'Race and Ethnicity'},
    {'value': 'Native Hawaiian and Other Pacific Islander alone, not Hispanic or Latino', 'label': 'Native Hawaiian and Other Pacific Islander alone, not Hispanic or Latino', 'group': 'Race and Ethnicity'},
    {'value': 'White alone, not Hispanic or Latino', 'label': 'White alone, not Hispanic or Latino', 'group': 'Race and Ethnicity'},
    {'value': 'Some other race alone, not Hispanic or Latino', 'label': 'Some other race alone, not Hispanic or Latino', 'group': 'Race and Ethnicity'},
    {'value': 'Two or more races, not Hispanic or Latino', 'label': 'Two or more races, not Hispanic or Latino', 'group': 'Race and Ethnicity'},
                
    {'value': 'Under 18 years', 'label': 'Under 18 years', 'group': 'Age'},
    {'value': '18 years and over', 'label': '18 years and over', 'group': 'Age'},
    {'value': '65 years and over', 'label': '65 years and over', 'group': 'Age'},
    {'value': 'Under 5 years', 'label': 'Under 5 years', 'group': 'Age'},
    {'value': '5 to 9 years', 'label': '5 to 9 years', 'group': 'Age'},
    {'value': '10 to 14 years', 'label': '10 to 14 years', 'group': 'Age'},
    {'value': '15 to 19 years', 'label': '15 to 19 years', 'group': 'Age'},
    {'value': '20 to 24 years', 'label': '20 to 24 years', 'group': 'Age'},
    {'value': '25 to 34 years', 'label': '25 to 34 years', 'group': 'Age'},
    {'value': '35 to 44 years', 'label': '35 to 44 years', 'group': 'Age'},
    {'value': '45 to 54 years', 'label': '45 to 54 years', 'group': 'Age'},
    {'value': '55 to 59 years', 'label': '55 to 59 years', 'group': 'Age'},
    {'value': '60 to 64 years', 'label': '60 to 64 years', 'group': 'Age'},
    {'value': '75 to 84 years', 'label': '75 to 84 years', 'group': 'Age'},
    {'value': '85 years and over', 'label': '85 years and over', 'group': 'Age'},

    {'value': 'Never married', 'label': 'Never married', 'group': 'Marital Status'},
    {'value': 'Now married', 'label': 'Now married', 'group': 'Marital Status'},
    {'value': 'Divorced', 'label': 'Divorced', 'group': 'Marital Status'},
    {'value': 'Separated', 'label': 'Separated', 'group': 'Marital Status'},
    {'value': 'Widowed', 'label': 'Widowed', 'group': 'Marital Status'},
    
    {'value': 'U.S. native', 'label': 'U.S. native', 'group': 'Citizenship and National Origin'},
    {'value': 'Born in the U.S.', 'label': 'Born in the U.S.', 'group': 'Citizenship and National Origin'},
    {'value': 'Born in New York', 'label': 'Born in New York', 'group': 'Citizenship and National Origin'},
    {'value': 'Born in a different state', 'label': 'Born in a different state', 'group': 'Citizenship and National Origin'},
    {'value': 'Born in Puerto Rico, U.S. Island areas, or abroad to American parent(s)', 'label': 'Born in Puerto Rico, U.S. Island areas, or abroad to American parent(s)', 'group': 'Citizenship and National Origin'},
    {'value': 'Foreign born', 'label': 'Foreign born', 'group': 'Citizenship and National Origin'},
    {'value': 'Naturalized U.S. citizen', 'label': 'Naturalized U.S. citizen', 'group': 'Citizenship and National Origin'},
    {'value': 'Not a U.S. citizen', 'label': 'Not a U.S. citizen', 'group': 'Citizenship and National Origin'},
    {'value': 'Foreign born, Europe', 'label': 'Foreign born, Europe', 'group': 'Citizenship and National Origin'},
    {'value': 'Foreign born, Asia', 'label': 'Foreign born, Asia', 'group': 'Citizenship and National Origin'},
    {'value': 'Foreign born, Africa', 'label': 'Foreign born, Africa', 'group': 'Citizenship and National Origin'},
    {'value': 'Foreign born, Oceania', 'label': 'Foreign born, Oceania', 'group': 'Citizenship and National Origin'},
    {'value': 'Foreign born, Latin America', 'label': 'Foreign born, Latin America', 'group': 'Citizenship and National Origin'},
    {'value': 'Foreign born, Northern America', 'label': 'Foreign born, Northern America', 'group': 'Citizenship and National Origin'},

    {'value': 'Entered U.S. 2010 or later', 'label': 'Entered 2010 or later', 'group': 'Period of U.S. Entry'},
    {'value': 'Entered U.S. 2000 to 2009', 'label': 'Entered 2000 to 2009', 'group': 'Period of U.S. Entry'},
    {'value': 'Entered U.S. 1990 to 1999', 'label': 'Entered 1990 to 1999', 'group': 'Period of U.S. Entry'},
    {'value': 'Entered U.S. before 1990', 'label': 'Entered before 1990', 'group': 'Period of U.S. Entry'},
    
    {'value': 'Lived in the same house 1 year ago', 'label': 'Same house', 'group': 'Residence 1 Year Ago'},
    {'value': 'Lived in a different house in the U.S. 1 year ago', 'label': 'Different house, in the U.S.', 'group': 'Residence 1 Year Ago'},
    {'value': 'Lived in a different house abroad 1 year ago', 'label': 'Different house, abroad', 'group': 'Residence 1 Year Ago'},
    
    {'value': 'Speak only English at home', 'label': 'Speak only English at home', 'group': 'Language'},
    {'value': 'Speak English less than "very well"', 'label': 'Speak English less than "very well"', 'group': 'Language'},
    {'value': 'Speak Spanish at home', 'label': 'Speak Spanish at home', 'group': 'Language'},
    {'value': 'Speak French, Haitian, or Cajun at home', 'label': 'Speak French, Haitian, or Cajun at home', 'group': 'Language'},
    {'value': 'Speak German or other West Germanic languages at home', 'label': 'Speak German or other West Germanic languages at home', 'group': 'Language'},
    {'value': 'Speak Russian, Polish, or other Slavic languages at home', 'label': 'Speak Russian, Polish, or other Slavic language at homes', 'group': 'Language'},
    {'value': 'Speak other Indo-European languages at home', 'label': 'Speak other Indo-European languages at home', 'group': 'Language'},
    {'value': 'Speak Korean at home', 'label': 'Speak Korean at home', 'group': 'Language'},
    {'value': 'Speak Chinese (incl. Mandarin, Cantonese) at home', 'label': 'Speak Chinese (incl. Mandarin, Cantonese) at home', 'group': 'Language'},    
    {'value': 'Speak Vietnamese at home', 'label': 'Speak Vietnamese at home', 'group': 'Language'},    
    {'value': 'Speak Tagalog (incl. Filipino) at home', 'label': 'Speak Tagalog (incl. Filipino) at home', 'group': 'Language'},    
    {'value': 'Speak other Asian and Pacific Island languages at home', 'label': 'Speak other Asian and Pacific Island languages at home', 'group': 'Language'},  
    {'value': 'Speak Arabic at home', 'label': 'Speak Arabic at home', 'group': 'Language'},    
    {'value': 'Speak other and unspecified languages at home', 'label': 'Speak other and unspecified languages at home', 'group': 'Language'},  
    
    {'value': 'Enrolled in nursery school, preschool', 'label': 'Nursery school or preschool', 'group': 'School Enrollment'},
    {'value': 'Enrolled in Kindergarten', 'label': 'Kindergarten', 'group': 'School Enrollment'},
    {'value': 'Enrolled in grades 1-8', 'label': 'Grades 1-8', 'group': 'School Enrollment'},
    {'value': 'Enrolled in grades 9-12', 'label': 'Grades 9-12', 'group': 'School Enrollment'},
    {'value': 'Enrolled in college or graduate school', 'label': 'College or graduate school', 'group': 'School Enrollment'},

    {'value': 'Less than 9th grade', 'label': 'Less than 9th grade', 'group': 'Educational Attainment'},
    {'value': '9th to 12th grade, no diploma', 'label': '9th to 12th grade, no diploma', 'group': 'Educational Attainment'},
    {'value': 'High school graduate', 'label': 'High school graduate', 'group': 'Educational Attainment'},
    {'value': 'Some college, no degree', 'label': 'Some college, no degree', 'group': 'Educational Attainment'},
    {'value': 'Associate\'s degree', 'label': "Associate's degree", 'group': 'Educational Attainment'},
    {'value': 'Bachelor\'s degree', 'label': "Bachelor's degree", 'group': 'Educational Attainment'},
    {'value': 'Graduate or professional degree', 'label': 'Graduate or professional degree', 'group': 'Educational Attainment'},

    {'value': 'Unemployment rate', 'label': 'Unemployment rate', 'group': 'Labor'},
    {'value': 'Employed', 'label': 'Employed', 'group': 'Labor'},
    {'value': 'Unemployed', 'label': 'Unemployed', 'group': 'Labor'},
    {'value': 'In the labor force', 'label': 'In the labor force', 'group': 'Labor'},
    {'value': 'Not in the labor force', 'label': 'Not in the labor force', 'group': 'Labor'},
    
    {'value': 'In the armed forces', 'label': 'In the armed forces', 'group': 'Military and Veterans'},
    {'value': 'Civilian veterans', 'label': 'Civilian veterans', 'group': 'Military and Veterans'},
    
    {'value': 'Employed in agriculture, forestry, fishing and hunting, and mining', 'label': 'Agriculture, forestry, fishing and hunting, and mining', 'group': 'Industry of Employment'},
    {'value': 'Employed in construction', 'label': 'Construction', 'group': 'Industry of Employment'},
    {'value': 'Employed in manufacturing', 'label': 'Manufacturing', 'group': 'Industry of Employment'},
    {'value': 'Employed in wholesale trade', 'label': 'Wholesale trade', 'group': 'Industry of Employment'},
    {'value': 'Employed in retail trade', 'label': 'Retail trade', 'group': 'Industry of Employment'},
    {'value': 'Employed in transportation and warehousing, and utilities', 'label': 'Transportation and warehousing, and utilities', 'group': 'Industry of Employment'},
    {'value': 'Employed in information', 'label': 'Information', 'group': 'Industry of Employment'},
    {'value': 'Employed in finance and insurance, and real estate and rental and leasing', 'label': 'Finance and insurance, and real estate and rental and leasing', 'group': 'Industry of Employment'},
    {'value': 'Employed in professional, scientific, and management, and administrative and waste management services', 'label': 'Professional, scientific, and management, and administrative and waste management services', 'group': 'Industry of Employment'},
    {'value': 'Employed in educational services, and health care and social assistance', 'label': 'Educational services, and health care and social assistance', 'group': 'Industry of Employment'},
    {'value': 'Employed in arts, entertainment, and recreation, and accommodation and food services', 'label': 'Arts, entertainment, and recreation, and accommodation and food services', 'group': 'Industry of Employment'},
    {'value': 'Employed in other services, except public administration', 'label': 'Other services, except public administration', 'group': 'Industry of Employment'},
    {'value': 'Employed in public administration', 'label': 'Public administration', 'group': 'Industry of Employment'},  
    
    {'value': 'Drive alone to work', 'label': 'Drive alone', 'group': 'Commute to Work'},
    {'value': 'Carpool to work', 'label': 'Carpool', 'group': 'Commute to Work'},
    {'value': 'Take public transit to work', 'label': 'Take public transit', 'group': 'Commute to Work'},
    {'value': 'Walk to work', 'label': 'Walk', 'group': 'Commute to Work'},
    {'value': 'Work from home', 'label': 'Work from home', 'group': 'Commute to Work'},
    
    {'value': 'Below 100 percent of the poverty level', 'label': 'Below 100 percent', 'group': 'Poverty Level'},
    {'value': '100 to 149 percent of the poverty level', 'label': '100 to 149 percent', 'group': 'Poverty Level'},
    {'value': 'At or above 150 percent of the poverty level', 'label': 'At or above 150 percent', 'group': 'Poverty Level'},
       
    {'value': 'With health insurance coverage', 'label': 'With health insurance coverage', 'group': 'Health Insurance'},
    {'value': 'With private health insurance', 'label': 'With private health insurance', 'group': 'Health Insurance'},
    {'value': 'With public coverage', 'label': 'With public coverage', 'group': 'Health Insurance'},
    {'value': 'No health insurance coverage', 'label': 'No health insurance coverage', 'group': 'Health Insurance'},
    
    {'value': 'With a disability', 'label': 'With a disability', 'group': 'Disability Status'},
    {'value': 'With a disability, under 18 years', 'label': 'With a disability, under 18 years', 'group': 'Disability Status'},
    {'value': 'With a disability, 18 to 64 years', 'label': 'With a disability, 18 to 64 years', 'group': 'Disability Status'},
    {'value': 'With a disability, 65 years and over', 'label': 'With a disability, 65 years and over', 'group': 'Disability Status'},

    {'value': '1-person households', 'label': '1-person households', 'group': 'Household Size'},
    {'value': '2-person households', 'label': '2-person households', 'group': 'Household Size'},
    {'value': '3-person households', 'label': '3-person households', 'group': 'Household Size'},    
    {'value': '4-or-more-person households', 'label': '4-or-more-person households', 'group': 'Household Size'},    

    {'value': 'Households with one or more people under 18 years', 'label': 'One or more people under 18 years', 'group': 'Household Age Composition'},
    {'value': 'Households with one or more people 65 years and over', 'label': 'One or more people 65 years and over', 'group': 'Household Age Composition'},
    
    {'value': 'Households with earnings', 'label': 'Households with earnings', 'group': 'Annual Household Income and Benefits'},
    {'value': 'Households with annual income and benefits of less than $10,000', 'label': 'Income and benefits of less than $10,000', 'group': 'Annual Household Income and Benefits'},
    {'value': 'Households with annual income and benefits of $10,000 to $14,999', 'label': 'Income and benefits of $10,000 to $14,999', 'group': 'Annual Household Income and Benefits'},
    {'value': 'Households with annual income and benefits of $15,000 to $24,999', 'label': 'Income and benefits of $15,000 to $24,999', 'group': 'Annual Household Income and Benefits'},
    {'value': 'Households with annual income and benefits of $25,000 to $34,999', 'label': 'Income and benefits of $25,000 to $34,999', 'group': 'Annual Household Income and Benefits'},
    {'value': 'Households with annual income and benefits of $35,000 to $49,999', 'label': 'Income and benefits of $35,000 to $49,999', 'group': 'Annual Household Income and Benefits'},
    {'value': 'Households with annual income and benefits of $50,000 to $74,999', 'label': 'Income and benefits of $50,000 to $74,999', 'group': 'Annual Household Income and Benefits'},
    {'value': 'Households with annual income and benefits of $75,000 to $99,999', 'label': 'Income and benefits of $75,000 to $99,999', 'group': 'Annual Household Income and Benefits'},
    {'value': 'Households with annual income and benefits of $100,000 to $149,999', 'label': 'Income and benefits of $100,000 to $149,999', 'group': 'Annual Household Income and Benefits'},
    {'value': 'Households with annual income and benefits of $150,000 to $199,999', 'label': 'Income and benefits of $150,000 to $199,999', 'group': 'Annual Household Income and Benefits'},
    {'value': 'Households with annual income and benefits of $200,000 or more', 'label': 'Income and benefits greater than or equal to $200,000', 'group': 'Annual Household Income and Benefits'},
    {'value': 'Households with retirement income', 'label': 'Households with retirement income', 'group': 'Annual Household Income and Benefits'},
    {'value': 'Households with Social Security', 'label': 'Households with Social Security', 'group': 'Annual Household Income and Benefits'},
    {'value': 'Households with Supplemental Security Income', 'label': 'Households with Supplemental Security Income', 'group': 'Annual Household Income and Benefits'},
    {'value': 'Households with cash public assistance income', 'label': 'Households with cash public assistance income', 'group': 'Annual Household Income and Benefits'},
    {'value': 'Households with Food Stamp/SNAP benefits in the past 12 months', 'label': 'Households with Food Stamp/SNAP benefits', 'group': 'Annual Household Income and Benefits'},

    {'value': 'Households with a mortgage', 'label': 'Households with a mortgage', 'group': 'Housing Tenure'},
    {'value': 'Occupied households paying rent', 'label': 'Households paying rent', 'group': 'Housing Tenure'},

    {'value': 'Households with SMOCAPI of less than 20.0 percent', 'label': 'Less than 20.0 percent', 'group': 'Selected Monthly Owner Costs as a Percentage of Household Income'},
    {'value': 'Households with SMOCAPI of 20.0 to 24.9 percent', 'label': '20.0 to 24.9 percent', 'group': 'Selected Monthly Owner Costs as a Percentage of Household Income'},
    {'value': 'Households with SMOCAPI of 25.0 to 29.9 percent', 'label': '25.0 to 29.9 percent', 'group': 'Selected Monthly Owner Costs as a Percentage of Household Income'},
    {'value': 'Households with SMOCAPI of 30.0 to 34.9 percent', 'label': '30.0 to 34.9 percent', 'group': 'Selected Monthly Owner Costs as a Percentage of Household Income'},
    {'value': 'Households with SMOCAPI of 35.0 percent or more', 'label': '35.0 percent or more', 'group': 'Selected Monthly Owner Costs as a Percentage of Household Income'},  

    {'value': 'Households with GRAPHI of less than 15.0 percent', 'label': 'Less than 15.0 percent', 'group': 'Gross Rent as Percentage of Household Income'},
    {'value': 'Households with GRAPHI of 15.0 to 19.9 percent', 'label': '15.0 to 19.9 percent', 'group': 'Gross Rent as Percentage of Household Income'},
    {'value': 'Households with GRAPHI of 20.0 to 24.9 percent', 'label': '20.0 to 24.9 percent', 'group': 'Gross Rent as Percentage of Household Income'},
    {'value': 'Households with GRAPHI of 25.0 to 29.9 percent', 'label': '25.0 to 29.9 percent', 'group': 'Gross Rent as Percentage of Household Income'},
    {'value': 'Households with GRAPHI of 30.0 to 34.9 percent', 'label': '30.0 to 34.9 percent', 'group': 'Gross Rent as Percentage of Household Income'},
    {'value': 'Households with GRAPHI of 30.0 to 34.9 percent', 'label': '35.0 percent or more', 'group': 'Gross Rent as Percentage of Household Income'},

    {'value': 'No vehicle available for household', 'label': 'No vehicles', 'group': 'Vehicles per Household'},
    {'value': '1 vehicle available for household', 'label': '1 vehicle', 'group': 'Vehicles per Household'},
    {'value': '2 vehicles available for household', 'label': '2 vehicles', 'group': 'Vehicles per Household'},
    {'value': '3 vehicles available for household', 'label': '3 vehicles', 'group': 'Vehicles per Household'},
    {'value': '4 or more vehicles available for household', 'label': '4 or more vehicles', 'group': 'Vehicles per Household'},

    {'value': 'Households with no telephone service available', 'label': 'Households with no telephone service available', 'group': 'Household Technology Access'},
    {'value': 'Households with a broadband Internet subscription', 'label': 'Households with a broadband Internet subscription', 'group': 'Household Technology Access'},
    {'value': 'Households with a computer', 'label': 'Households with a computer', 'group': 'Household Technology Access'},

    {'value': 'Utility gas used as household heat source', 'label': 'Utility gas', 'group': 'Household Heat Source'}, 
    {'value': 'Bottled, tank, or LP gas used as household heat source', 'label': 'Bottled, tank, or LP gas', 'group': 'Household Heat Source'},    
    {'value': 'Electricity used as household heat source', 'label': 'Electricity', 'group': 'Household Heat Source'}, 
    {'value': 'Fuel oil, kerosene, etc. used as household heat source', 'label': 'Fuel oil, kerosene, etc.', 'group': 'Household Heat Source'},       
    {'value': 'Coal or coke used as household heat source', 'label': 'Coal or coke', 'group': 'Household Heat Source'},       
    {'value': 'Wood used as household heat source', 'label': 'Wood', 'group': 'Household Heat Source'},    
    {'value': 'Solar energy used as household heat source', 'label': 'Solar energy', 'group': 'Household Heat Source'},        
    {'value': 'Other fuel used as household heat source', 'label': 'Other fuel', 'group': 'Household Heat Source'},       
    {'value': 'No fuel used by household', 'label': 'No fuel used', 'group': 'Household Heat Source'},   
                                  
]

# creating a version without income variables for chart view, because they cannot be compared over time due to inflation
no_income_dropdown_dict = deepcopy(dropdown_dict)
no_income_dropdown_dict = [item for item in no_income_dropdown_dict if '$' not in item['label']]        

# %%
# dict of geography options/ values used to create dynamic dropdown in the Dash App
# using acs_years[-1] to get the most recent year's set of regions (all years do share the same set of regions, so pretty much just doing this for consistency)
    
all_options = {'Council District (2023 Boundaries)': globals()[f'councildist_2023_geographies_{acs_years[-1]}']['councildist_2023'].to_list(),
               'Council District (2013 Boundaries)': globals()[f'councildist_2013_geographies_{acs_years[-1]}']['councildist_2013'].to_list(),
               'Community District': globals()[f'communitydist_geographies_{acs_years[-1]}']['communitydist'].to_list(),
               'School District': globals()[f'schooldist_geographies_{acs_years[-1]}']['schooldist'].to_list(),
               'Police Precinct': globals()[f'policeprct_geographies_{acs_years[-1]}']['policeprct'].to_list(),
               'Modified ZIP Code Tabulation Area': globals()[f'modzcta_geographies_{acs_years[-1]}']['modzcta'].to_list(),
               'Neighborhood Tabulation Area': sorted(globals()[f'nta_geographies_{acs_years[-1]}']['nta'].to_list()),
               'Borough': sorted(globals()[f'borough_geographies_{acs_years[-1]}']['borough'].to_list())} 

# adding NYC as option for tabs 2 and 3

all_options_add_nyc = deepcopy(all_options)
all_options_add_nyc['New York City'] = ['N/A']

# %%
# setting initial map view for the dashboard
# using acs_years[-1] to access the most recent year for the default map

orig_map = folium_plot('Total population: Data Profiles 5-Year', 'councildist_2023', deepcopy(globals()[f'councildist_2023_geographies_{acs_years[-1]}']), 'Numbers', deepcopy(globals()[f'name_to_code_dict_{acs_years[-1]}']), deepcopy(globals()[f'name_to_denom_dict_{acs_years[-1]}']))

# %%
# NYC logo, to be added to dashboard

data_team_logo = '../code/assets/data-council-logo.png'
# NYCC_logo = '../code/assets/NYCC-logo.png'

# %%
# markdown text for pop-ups

contact_markdown_content = """
Can't find the data you're looking 
for? Have any questions, comments, 
or concerns? Please reach out to 
[datainfo@council.nyc.gov](mailto:datainfo@council.nyc.gov)  
with any feedback.
"""

rel_markdown_content = """
## **Statistical Reliability Measures**

**MOE:** Margin of Error. A 90% confidence interval for the estimate.

**CV:** Coefficient of Variation. The ratio of the standard deviation to the mean. Estimates 
with a CV of 20 or greater are not considered statistically reliable, as indicated with an asterisk.

"""

demo_markdown_content = """
All variables in this dropdown menu come from the [5-Year American Community Survey](https://www.census.gov/data/developers/data-sets/acs-5year.html) Data Profiles datasets, which provide social, economic, housing, and demographic estimates by census tract."""

time_markdown_content = """
This dashboard utilizes estimates from the [5-Year American Community Survey](https://www.census.gov/data/developers/data-sets/acs-5year.html), which provides "period" estimates representing data collected over a period of time. This means that all data points presented on CouncilCount are akin to 5-year averages for the selected time period.
"""

difference_markdown_content = """
**Difference:** The first estimate subtracted by the second estimate. Asterisks in this column indicate that 1) one of the two estimates is not statistically reliable and/ or 2) the difference between the two values is not significant due to their confidence intervals (MOEs) overlapping. If a cell in the Difference column is blank, it means that the reliability of the difference value could not be determined due to missing data.
"""

# %%
# markdown text for About Page (tab 4)

how_to_markdown_content="""
Welcome to CouncilCount, a dashboard designed to make exploring New York City’s diverse population simple! There are three options for interacting with the data: Map View, Table View, and Chart View.
"""

map_view_markdown_content="""
Map View displays a choropleth map for a chosen demographic variable along specified geographic boundaries. As indicated by the legend on the map, darker blues represent higher values—in this case, a higher population of the given demographic group residing within a region’s boundaries. Using the dropdown menus to the right of the map, set the demographic variable, geography, time period, and measure (either “Numbers”—total number of people with the chosen demographic characteristic in the region—or “Percents”—the number value divided by the region’s total population, unless otherwise specified). Some demographics, like total population, only have one measure available (in this case, “Numbers”). In some cases, data may not be available for a particular variable at the chosen time period. In these scenarios, a message will appear on the map window indicating the lack of available data. Regions with estimates that are not statistically reliable are displayed in grey. A file containing the data used to generate the choropleth for the selected geography and time period, along with a data dictionary, may be downloaded by clicking the button located at the bottom left of the map. 

In the “Regional Comparison Table” table located at the bottom right of the page, users can compare individual geographic regions to New York City, and to each other, for the selected demographic. This table can be sorted low to high, high to low, or by region name. An asterisk next to an estimate indicates that the data point is not statistically reliable. This table can be downloaded by clicking the “export” button at its bottom left. 
"""

table_view_markdown_content="""
Table View allows users to dive deeper into comparing two geographic regions, rather than viewing the distribution of one demographic group across the entire city. Table View provides a table comparing the two selected geographic regions on multiple demographic variables during one time period. The default subjects shown in the table are Population, Ethnicity, Race, and Sex. To update the table, add or delete subjects from the “Select Areas of Interest” dropdown menu. The “Difference” column presents the difference between two estimates, subtracting the first value from the second. If data is unavailable for a certain variable within a particular time period, the associated cells will remain blank. An asterisk next to an estimate, or difference between estimates, in the table indicates that the data point is not statistically reliable. The table may be exported at any time using the button located at the table’s bottom left. 
"""

chart_view_markdown_content="""
Chart View provides a line chart that visualizes demographic trends over the course of up to three time periods in one selected region. Household income variables are excluded from Chart View because all dollar amounts are inflation-adjusted to the final year of their respective 5-year ACS period. This means values from different time periods are not directly comparable in real terms. Error bars in Chart View represent the margin of error for each point. If the error bars on any two points overlap, the difference between these values is not considered statistically significant. Individual data points that are not statistically reliable are displayed in gray on the chart. Missing data points will not appear in the chart. To download the visual as a PNG, navigate to the top right of the chart and click on the camera icon that appears.
"""

data_reliability_note = """
Note: To learn more about the statistical reliability measures used in CouncilCount, please view the section titled “Data Reliability.”
"""

background_markdown_content = """
The [American Community Survey (ACS)][1] is the largest household survey conducted by the U.S. Census Bureau. The annual survey, which is sent to about 3.5 million addresses per year in the 50 states, the District of Columbia, and Puerto Rico, collects detailed demographic information about the nation’s population, including race and ethnicity, educational attainment, employment, income, and many more subject areas. 

CouncilCount utilizes the [5-Year ACS][2], meaning the data points presented on the dashboard represent 5-year averages for the listed demographic variables. Using the multiyear estimates increases the statistical reliability of the data, especially for small population subgroups and regions with low populations. 

The 5-Year ACS provides demographic estimates by census tract for thousands of variables. Estimates for some geographies, like neighborhood tabulation areas, which are built from census tracts, may be generated by directly aggregating census-tract-level data. However, this method does not work for geographies that have no relation to census tracts, like council districts and police precincts. In order to generate estimates for such geographies, ACS demographic data was synthesized with building data from the [Primary Land Use Tax Lot Output (PLUTO) datasets][3] to approximate the distribution of subpopulations around the city for each time period. For more information on the method used to generate the demographic estimates presented on CouncilCount, please contact [DataOperationsUnit@council.nyc.gov](mailto:DataOperationsUnit@council.nyc.gov).

[1]: https://www.census.gov/programs-surveys/acs/about.html   
[2]: https://www.census.gov/data/developers/data-sets/acs-5year.html 
[3]: https://www.nyc.gov/site/planning/data-maps/open-data/dwn-pluto-mappluto.page 
"""

variable_markdown_content = """
All demographic variables featured on CouncilCount are drawn from the Detailed Tables, Subject Tables, or Data Profiles ACS 5-Year surveys. Visit [this link][4] to view the data dictionaries for these surveys, which display all the variables that can be accessed via the Census Data API. Many of these variables, when pulled from the API in percent form, are provided with denominators other than the total population. Therefore, when “Percents” is selected on the Map or Chart View tab, information about the denominator will be presented along with the visuals. This information is not available on the Table View tab, but a file that includes CouncilCount’s data dictionary, which provides denominator information, can be downloaded on the Map View page by clicking the button located at the bottom left of the map.

**Here is a list of the CouncilCount variable categories that provide estimates at the person-level:**
* Age
* Citizenship and National Origin
* Commute to Work
* Disability Status
* Educational Attainment
* Ethnicity
* Health Insurance
* Industry of Employment
* Labor
* Language
* Marital Status
* Military and Veterans
* Period of U.S. Entry
* Poverty Level
* Race
* Race and Ethnicity
* Residence 1 Year Ago
* School Enrollment
* Sex

**Here is a list of the CouncilCount variable categories that provide estimates at the household-level:**
* Annual Household Income and Benefits
* Gross Rent as Percentage of Household Income
* Household Age Composition
* Household Heat Source
* Household Size
* Household Technology Access
* Housing Tenure
* Selected Monthly Owner Costs as a Percentage of Household Income

[4]: https://api.census.gov/data/2023/acs/acs5.html 

"""

data_reliability_markdown_content = """
Margins of error (MOEs) and coefficients of variation (CVs) are provided for all estimates on CouncilCount to help users assess the level of trust that they can place in a given data point. 

The ACS samples about 1% of the entire U.S. population to generate its data, making all values merely estimates. To account for sampling variability in ACS data, all estimates in ACS datasets are accompanied with MOEs that provide a 90% confidence interval. This means that, for a given estimate, there is a 90% chance that the true population value falls within the range of the estimate plus or minus the MOE. 

MOEs are used to determine the statistical significance of differences between two values. The difference between two values is only considered significant if their confidence intervals do not overlap.

CV, another reliability measure, places the MOE in context by dividing the sample’s standard deviation by its mean. Individual estimates with a CV of 20 or greater are not considered statistically reliable for most applications. As described previously, estimates displayed with asterisks in the tables, regions colored in grey on the map, and data points colored grey in the line chart are not statistically reliable based on their CV. Values in Table View’s Difference column will also receive an asterisk if at least one estimate is statistically unreliable due to a high CV.

Data points for regions with smaller populations tend to be less statistically reliable. If an individual data point, or the difference between two data points, is not statistically reliable for the selected region, consider selecting a larger geography (community district instead of neighborhood tabulation area, for example). 

More information about reliability measures used by the Census Bureau can be found [here][5]. 

[5]: https://www.census.gov/content/dam/Census/library/publications/2018/acs/acs_general_handbook_2018_ch07.pdf 
"""

geo_marker_content_note = """
Note: Estimates for all geographies (except for council districts) are only available along boundary lines as they were drawn in 2020, regardless of the period chosen, in order to make comparisons possible across time. For some geographies, like boroughs, this is not particularly relevant, given that their boundaries do not change. However, boundary lines for geographies like neighborhood tabulation areas have changed as recently as 2020, making it difficult to compare these regions over time without holding boundary lines static. As for council districts, all estimates are available along either 2013 or 2023 boundary lines.
"""

geo_markdown_content = """
# **CouncilCount Geographies**

Note: Estimates for all geographies (except for council districts) are only available along boundary lines as they were drawn in 2020, regardless of the period chosen, in order to make comparisons possible across time. For some geographies, like boroughs, this is not particularly relevant, given that their boundaries do not change. However, boundary lines for geographies like neighborhood tabulation areas have changed as recently as 2020, making it difficult to compare these regions over time without holding boundary lines static. As for council districts, all estimates are available along either 2013 or 2023 boundary lines.

**Council Districts:** 
NYC has 51 council districts, each of which is represented by a member elected to the New York City Council. Council district estimates were generated by synthesizing data from the ACS and PLUTO. The page offers the option to use 2013 or 2023 council district boundaries.

**Community Districts:** 
NYC-created geography. NYC is divided into 59 CDs, which have appointed advisory groups called community boards. CD estimates were generated by synthesizing data from the ACS and PLUTO. 12 “joint interest areas," which are large parks or airports that are not considered part of any community district, are excluded from the dashboard visuals. 

**School Districts:** 
NYC Department of Education school districts. School district estimates were generated by synthesizing data from the ACS and PLUTO.

**Police Precincts:** 
NYC has 77 police precincts, each of which is patrolled by a designated police unit. Precinct estimates were generated by synthesizing data from the ACS and PLUTO. Precinct 22, which represents Central Park, is excluded from the dashboard visuals.

**ZIP Codes:**
ZIP codes are ​​a set of digits used to identify a postal delivery area. Due to the instability of traditional ZIP codes, which are frequently realigned, merged, or split, CouncilCount uses a variation of ZIP codes called Modified Zip Code Tabulation Areas (MODZCTA). To generate ZIP Code Tabulation Areas, or ZCTAs, the Census Bureau combined census blocks that shared roughly the same ZIP codes, which created geographic regions that were more stable and better aligned with the census hierarchy. MODZCTAs combine ZCTAs with populations under 3,000 to facilitate more meaningful population-based analysis. All MODZCTA estimates in CouncilCount are available along 2020 MODZCTA boundary lines. Since 2020 MODZCTAs are built directly from 2020 ZCTAs, estimates for survey years post-2020 were generated by aggregating ACS data available by ZCTA to the MODZCTA-level. This is not possible for the pre-2020 time periods, given that ACS 5-Year data for these years are only available by earlier ZCTA boundaries, making it challenging to directly aggregate this data to 2020 MODZCTA boundaries. Therefore, MODZCTA estimates for these time periods were generated by synthesizing data from the ACS and PLUTO, given that the original data is not available at geography levels that directly relate to the 2020 census hierarchy. MODZCTA 99999, which represents some of the city’s parks, is excluded from the dashboard visuals.

**Neighborhood Tabulation Areas:** 
NYC Department of City Planning-developed geographies that intend to approximate city neighborhoods. All NTA estimates in CouncilCount are available along 2020 NTA boundary lines. Since 2020 NTAs are built directly from 2020 census tracts, estimates for survey years post-2020 were generated by aggregating ACS data available by 2020 census tract to the NTA-level. This is not possible for the pre-2020 time periods, given that ACS 5-Year data for these years are only available by earlier census tract boundaries, making it challenging to directly aggregate this data to 2020 NTA boundaries. Therefore, NTA estimates for these time periods were generated by synthesizing data from the ACS and PLUTO, given that the original data is not available at geography levels that directly relate to the 2020 census hierarchy. NTAs with low populations, such as parks, graveyards, and airports, are excluded from the dashboard visuals. 

**Boroughs:** Includes The Bronx, Brooklyn, Manhattan, Queens, and Staten Island, all of which are conterminous with a respective New York State county. These estimates were directly taken from the ACS, which provides data at the county-level. 

**New York City:** Citywide estimates were taken directly from the ACS, which provides data for New York City. 

To learn more about New York City geographies, please visit [this guide][6] from the NYC Department of City Planning’s website.

[6]: https://storymaps.arcgis.com/stories/d30850ba28944619b94e8ee4f746d5c4   
"""

# %%
# CSS styling for pop-ups in Dash app

popover_style = {'background-color': '#ffffff',
                 'max-width':'500px',
                 'font-size':'14px',
                 'font-family': 'sans-serif',
                 'border': '1px solid rgba(0, 0, 0, 0.15)',
                 'box-shadow':'0 0.5rem 1rem rgba(0, 0, 0, 0.15)',
                 'padding': '0.3cm',
                 'body-color':'#212529',
                 'color':'black',
                 'border-radius':'0.5rem',
                 'inner-border-radius':'calc(0.5rem - 1px)',
                }

popover_style_small = popover_style.copy()
popover_style_small['max-width'] = '280px'

popover_style_med = popover_style.copy()
popover_style_med['max-width'] = '350px'

# %%
# creating app

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css',
                        'https://codepen.io/chriddyp/pen/brPBPO.css',
                        dbc.themes.BOOTSTRAP]

app = dash.Dash(__name__,
                external_stylesheets=external_stylesheets, # adding stylesheets
                meta_tags=[ 
                    {"name": "viewport", "content": "width=device-width, initial-scale=0.65"} # making app mobile-friendly
                    ],
                )

#app.config.suppress_callback_exceptions = True

# %%
# establishing the Dash App's various components
       
# setting the webpage titles/ headings
    
header_top_1 = html.Div( # NYC Council Data Team Logo
                html.Img(src=b64_image(data_team_logo), style={'height':'30%', 'width':'30%', 'float':'left', 'margin-top': '0.5cm', 'margin-bottom':'0.25cm', 'margin-right':'0.1cm'})
             ), 
                    
header_top_2 = html.Div([ # info on how to contact Data Team with questions
                    html.Abbr('\u24D8', id='contact-info-tooltip', style={'fontSize':'25px', 'float':'right', 'margin-right':'35%'}),
                        dbc.Popover(
                            [dbc.PopoverBody(dcc.Markdown(contact_markdown_content))],
                            target='contact-info-tooltip',
                            trigger='hover',
                            placement='left', 
                            style=popover_style_small
                        ),
                ]),

header_bottom = html.Div( # horizontal line
                    dbc.Row(html.Hr(style={'border-top': '1px solid black', 'width': '100%', 'float':'left', 'margin-bottom':'0.25cm'}))
                ), 

#### layout components for tab 1

# adding the default choropleth map (folium)   
    
the_map = html.Div([
    
            # map
            
            html.Div(
                html.Iframe(id = 'the_map', srcDoc = open(orig_map, 'r').read(), width = '100%', height = '630',
                          style={'border':'0.25px solid gray', 'overflow': 'auto', 'margin-bottom': '0.2cm'}),
            ),
      
            # note about reliability
    
            html.Div(
               html.H1(children="Note: Regions shown in grey have poor statistical reliability (CV >= 20)", 
                    style={"fontSize": "14px", 'font-family':'Gotham Light', 'fontWeight': 'bold', "text-align": "left", 'margin-bottom': '0.25cm'}
                   )
            ),

            # button to allow download of data table

            html.Div([
                html.Button('Download Data', id='btn_excel', 
                    style={'background-color': 'none', 
                           'border': 'none',
                           'outline': 'none',
                           'color': 'blue',
                           'padding': '0cm',
                           'text-decoration': 'underline',
                           'font-size': '14px',
                           'font-family': 'Gotham Medium',
                           'float': 'left',
                           'margin-bottom': '0.5cm'
                          }),
            dcc.Download(id="download-dataframe-excel"),
        ]),
    ]),

the_regional_table = html.Div([                
    
            # header for table 
    
            html.Div(
                html.H1(children="REGIONAL COMPARISON TABLE", 
                        style={"fontSize": "20px", 'font-family': 'Bell Gothic Std Black', "color": "black",
                                "text-align": "left", 'margin-bottom':'0.25cm'}),   

            ),


            # dynamic header for region dropdown (will change based on geo-selection-input_tab1, e.g. 'Select a Council District')

            html.Div([

                html.Div(
                    id='geo_header_tab1',
                    style={'margin-bottom':'0.1cm', 'margin-right':'0.5cm'}
                ),

                # dynamic dropdown menu for regions within NYC (will change based on geo-selection-input, e.g. listing all council districts)  

                dcc.Dropdown(
                    id='geo-num-selection-input_tab1',
                    searchable = True,
                    clearable = False,
                    multi=True,
                    style = {"color": 'black',#"#499ED5", 
                            'fontSize': '16px',
                            'font-family': 'sans-serif',
                            'margin-bottom': '0.35cm',
                            'margin-right': '0.5cm',
                            #'width':'100%',
                            }
                    ),

                html.Div([

                    # header for sort options

                    html.H1(children="Sort Table:", 
                            style={"fontSize": "18px", 'font-family': 'Gotham Medium', "color": "black", 
                                    "text-align": "left", 'margin-bottom': '0.1cm', 'margin-right': '0.5cm'}),

                    # ratio button options to sort regional comparison table

                    dcc.RadioItems(
                        id='rank-selection-input_tab1',
                        options=[
                            {"label": html.Span("By region", style={"margin-right": "20px"}), "value": None},
                            {"label": html.Span("Low to high", style={"margin-right": "20px"}), "value": False},
                            {"label": "High to low", "value": True}
                            ],
                        value=None,
                        inline=True,
                        inputStyle={"margin-right": "5px"}, # space between text and buttons
                        style={
                            "color": 'black',
                            'fontSize': '16px',
                            'font-family': 'sans-serif',
                            'margin-bottom': '0.35cm'
                        }
                    )
                ]),

                html.Abbr('\u24D8', id='rel-info-tooltip', style={'float':'right', 'fontSize':'15px'}), # adding tooltip that will provide info upon hover
                        dbc.Popover(
                            [dbc.PopoverBody(dcc.Markdown(rel_markdown_content))],
                            target='rel-info-tooltip',
                            trigger='hover',
                            placement='left', 
                            style=popover_style_med
                        ),  

                # creating a table that will compare an individual geography's demographics to NYC-wide numbers

                html.Div(
                    id = 'map_tableDiv',
                    children = '',
                    style={'font-family': 'Gotham Medium',
                            'margin-bottom': '0.2cm'}
                ),

                html.Div( # 'poor statistical reliability' text will appear if any estimates are statistically unreliable
                        id='reliability_text_tab1',
                        style={"fontSize": "13px", 
                                'font-family':'Gotham Light', 
                                'fontWeight': 'bold',
                                'float': 'right'
                                }          
                    ),  

            ],

        style={'margin-bottom': '4cm'} 
                
        ),   
    ]),

# dropdown menus

map_dropdowns = html.Div([
        
                # page heading
        
                html.Div(
                    html.H1(children="MAP DEMOGRAPHICS", 
                            style={"fontSize": "20px", 'font-family': 'Bell Gothic Std Black', 
                                   "color": "black", "text-align": "left", 'margin-bottom': '0.25cm'}),
                    ),
 
                # creating a dropdown menu with demographic variable options 
    
                html.Div([
                    
                    html.H1(children="Select Demographic:", 
                        style={"fontSize": "18px", 'font-family': 'Gotham Medium', "color": "black", "text-align": "left", 
                               'margin-right': '0.25cm', 'margin-bottom': '0.1cm'}),
                    
                    html.Abbr('\u24D8', id='demo-info-tooltip', style={'fontSize':'15px', 'margin-right': '0.25cm', 'margin-top':'-5px'}), # adding tooltip that will provide info upon hover
                        dbc.Popover(
                            [dbc.PopoverBody(dcc.Markdown(demo_markdown_content))],
                            target='demo-info-tooltip',
                            trigger='hover',
                            placement='left', 
                            style=popover_style_med
                        )
                    
                    ],

                    # placing the header and the info button next to each other 

                    style={
                       'display': 'flex',
                       'flex-direction': 'row',
                       'align-items': 'center',
                      }
                    
                    ),
                    
                html.Div(
                    dmc.Select(
                        placeholder='Select...',
                        id='demo-selection-input_tab1', # name of the selected inputs from the demo dropdown
                        searchable = True,
                        clearable = False,
                        value='Total population: Data Profiles 5-Year', # starting value is Total population 
                        data=dropdown_dict,
                        style={'font-family':'sans-serif', 'fontSize': '16px', 'margin-bottom': '0.65cm'}
                    ), 

            ),
    
                # geography dropdown menu 
    
                html.Div([

                    html.H1(children="Select Geography:", 
                            style={"fontSize": "18px", 'font-family': 'Gotham Medium', "color": "black", 
                                   "text-align": "left", 'margin-bottom': '0.1cm', 'margin-right': '0.5cm'}),

                    dcc.Dropdown(
                        id='geo-selection-input_tab1',
                        searchable = True,
                        clearable = False,
                        value = 'Council District (2023 Boundaries)',
                        options = list(all_options.keys()), 
                        style = {"color": 'black',#"#499ED5", 
                                 'fontSize': '16px',
                                 'font-family': 'sans-serif',
                                 'margin-bottom': '0.65cm',
                                }
                        ),
                
                    ]), 
            
                # allowing choice of time period
    
                html.Div([ 
                    
                    html.H1(children="Select Time Period:", 
                        style={"fontSize": "18px", 'font-family': 'Gotham Medium', "color": "black", 
                               'float': 'left', "text-align": "left", 'margin-bottom': '0.1cm', 'margin-right': '0.25cm'}),

                    html.Abbr('\u24D8', id='time-info-tooltip', style={'fontSize':'15px', 'margin-right':'0.25cm', 'margin-top':'-5px'}), # adding tooltip that will provide info upon hover
                        dbc.Popover(
                            [dbc.PopoverBody(dcc.Markdown(time_markdown_content))],
                            target='time-info-tooltip',
                            trigger='hover',
                            placement='left', 
                            style=popover_style_med
                        ),                   
    
                    ],
                
                    # placing the header and the info button next to each other 

                    style={
                       'display': 'flex',
                       'flex-direction': 'row',
                       'align-items': 'center',
                      }
                
                    ), 
    
                    html.Div(
                        dcc.Dropdown(
                        id='time-selection-input_tab1',
                        searchable = True,
                        clearable = False,
                        value = time_periods[-1], # most recent time period
                        options = time_periods,
                        style = {"color": 'black',#"#499ED5", 
                                 'fontSize': '16px',
                                 'font-family': 'sans-serif',
                                 'margin-bottom': '0.65cm',
                                }
                        )
                    ),
    
                # allowing choice between numbers and percents
                
                html.Div([
                    
                    html.H1(children="Select Measure:", 
                            style={"fontSize": "18px", 'font-family': 'Gotham Medium', "color": "black", 
                                   "text-align": "left", 'margin-bottom': '0.1cm', 'margin-right': '0.5cm'}),


                    # dynamic dropdown menu for metrics (demo inputs like 'total population' only have number estimates available)   

                    dcc.Dropdown(
                        id='metric-selection-input_tab1',
                        searchable = True,
                        clearable = False,
                        # options=['Numbers','Percents'], commented out because callback takes care of this now 
                        # value='Numbers', 
                        style = {"color": 'black',#"#499ED5", 
                                 'fontSize': '16px',
                                 'font-family': 'sans-serif',
                                 'margin-bottom': '0.65cm',
                                }
                        ), 

                    ],

#                     style={'display':'inline-block','width': '100%'} 

                ),
    
            #     # header for table 
    
            #     html.Div(
            #         html.H1(children="REGIONAL COMPARISON TABLE", 
            #                 style={"fontSize": "20px", 'font-family': 'Bell Gothic Std Black', "color": "black",
            #                        "text-align": "left", 'margin-bottom':'0.25cm'}),   

            #     ),


            #     # dynamic header for region dropdown (will change based on geo-selection-input_tab1, e.g. 'Select a Council District')

            #     html.Div([

            #         html.Div(
            #             id='geo_header_tab1',
            #             style={'margin-bottom':'0.1cm', 'margin-right':'0.5cm'}
            #         ),

            #         # dynamic dropdown menu for regions within NYC (will change based on geo-selection-input, e.g. listing all council districts)  

            #         dcc.Dropdown(
            #             id='geo-num-selection-input_tab1',
            #             searchable = True,
            #             clearable = False,
            #             multi=True,
            #             style = {"color": 'black',#"#499ED5", 
            #                     'fontSize': '16px',
            #                     'font-family': 'sans-serif',
            #                     'margin-bottom': '0.35cm',
            #                     'margin-right': '0.5cm',
            #                     #'width':'100%',
            #                     }
            #             ),

            #         html.Div([

            #             # header for sort options

            #             html.H1(children="Sort Table:", 
            #                     style={"fontSize": "18px", 'font-family': 'Gotham Medium', "color": "black", 
            #                             "text-align": "left", 'margin-bottom': '0.1cm', 'margin-right': '0.5cm'}),

            #             # ratio button options to sort regional comparison table

            #             dcc.RadioItems(
            #                 id='rank-selection-input_tab1',
            #                 options=[
            #                     {"label": html.Span("By region", style={"margin-right": "20px"}), "value": None},
            #                     {"label": html.Span("Low to high", style={"margin-right": "20px"}), "value": False},
            #                     {"label": "High to low", "value": True}
            #                     ],
            #                 value=None,
            #                 inline=True,
            #                 inputStyle={"margin-right": "5px"}, # space between text and buttons
            #                 style={
            #                     "color": 'black',
            #                     'fontSize': '16px',
            #                     'font-family': 'sans-serif',
            #                     'margin-bottom': '0.35cm'
            #                 }
            #             )
            #         ]),
    
            #         html.Abbr('\u24D8', id='rel-info-tooltip', style={'float':'right', 'fontSize':'15px'}), # adding tooltip that will provide info upon hover
            #                 dbc.Popover(
            #                     [dbc.PopoverBody(dcc.Markdown(rel_markdown_content))],
            #                     target='rel-info-tooltip',
            #                     trigger='hover',
            #                     placement='left', 
            #                     style=popover_style_med
            #                 ),  

            #         # creating a table that will compare an individual geography's demographics to NYC-wide numbers

            #         html.Div(
            #             id = 'map_tableDiv',
            #             children = '',
            #             style={'font-family': 'Gotham Medium',
            #                    'margin-bottom': '0.2cm'}
            #         ),

            #         html.Div( # 'poor statistical reliability' text will appear if any estimates are statistically unreliable
            #                 id='reliability_text_tab1',
            #                 style={"fontSize": "13px", 
            #                        'font-family':'Gotham Light', 
            #                        'fontWeight': 'bold',
            #                        'float': 'right'
            #                        }          
            #             ),  

            #     ],

            # style={'margin-bottom': '4cm'} 
                    
            # ),          
        ],

        className = 'float-child',
        style={'flex': '1'}, 
    )

#### layout components for tab 2

the_table = html.Div([ # dynamic table for tab2 
    
                # table headings
    
                html.Div([
                    
                    # dynamic table label
                    
                    html.Div(
                        id='table_label',
                        style={'display':'inline-block'}, 
                    ),
                    
                    html.Div([
                        
                        # check box letting users choose whether or not reliability data will be shown
                        
                        dcc.Checklist( 
                            id='rel-check-box',
                            options=[{'label':' View reliability data', 'value':'check-yes'}],
                            value=['check-yes'],
                            style={'float':'right', 'display':'inline-block'},
                            labelStyle={'font-family':'Gotham Light', 'fontWeight': 'bold', 'fontSize': '13px', 'align-items': 'center'},
                                ),
                        
                        # reliability message

                        html.Abbr('\u24D8', id='rel-info-tooltip', style={'float':'right', 'margin-left':'0.2cm', 'margin_top':'-5px', 'fontSize':'15px'}), # adding tooltip that will provide info upon hover
                            dbc.Popover(
                                [dbc.PopoverBody(dcc.Markdown(rel_markdown_content + difference_markdown_content))],
                                target='rel-info-tooltip',
                                trigger='hover',
                                placement='left', 
                                style=popover_style_med
                            ),
                        
                    ],
                    
                    style={'display':'flex'},
                    
                    ),

                ],
                
                style={'display':'flex', 'justify-content': 'space-between'}
                # style={'display':'flex', 'margin-bottom': '0.1cm', 'justify-content': 'space-between'}
                    
                ),
    
                # table
    
                html.Div(
                    id = 'table_tableDiv',
                    children = '',
                    #className = 'tableDiv',
                    style={'font-family': 'Gotham Medium',
                           #'margin-bottom': '0.2cm',
                           }
                ),
    
                # reliability message
    
                html.Div( # 'poor statistical reliability' text will appear if unreliable data is in table
                        id='reliability_text_tab2',
                        style={"fontSize": "13px", 
                               'float':'right',
                               'font-family':'Gotham Light', 
                               'fontWeight': 'bold',
                               'margin-bottom': '0.4cm'
                               }          
                    ),
                    
            ])

table_dropdowns = html.Div([
    
                    # page heading
    
                    html.Div(
                        html.H1(children="DEMOGRAPHIC DEEP DIVE", 
                            style={"fontSize": "20px", 'font-family': 'Bell Gothic Std Black', "color": "black", 
                                   "text-align": "left", 'margin-bottom': '0.25cm'})
                             ),
                        
                     # creating a dropdown menu with group options
                        
                    html.Div([
                        
                        html.H1(children="Select Areas of Interest:",
                              style={"fontSize": "18px", 'font-family': 'Gotham Medium', "color": "black", 
                                     "text-align": "left", 'margin-right':'0.25cm','margin-bottom': '0.1cm'}), 
                        
                        # adding tooltip that will provide info upon hover
                        html.Abbr('\u24D8', id='demo-info-tooltip', style={'fontSize':'15px', 'margin-right':'0.25cm','margin-top': '-5px'}), 
                            dbc.Popover(
                                [dbc.PopoverBody(dcc.Markdown(demo_markdown_content))],
                                target='demo-info-tooltip',
                                trigger='hover',
                                placement='left', 
                                style=popover_style_med
                            ),
                    
                        ],   

                        # placing the header and the info button next to each other 
                        
                        style={
                           'display': 'flex',
                           'flex-direction': 'row',
                           'align-items': 'center',
                          }

                        ),
                        
                    html.Div(
                        
                        dmc.MultiSelect(
                            placeholder='Select...',
                            id='group-selection-input', # name of the selected inputs from the demo dropdown
                            searchable = True,
                            clearable = False,
                            value=['Population', 'Sex', 'Ethnicity', 'Race'], # starting values
                            data=list(pd.DataFrame(dropdown_dict).group.unique()),
                            style={'font-family':'sans-serif','margin-bottom': '0.5cm'}
                        )
                    ),
    
                    # geography dropdown menu #1

                    html.Div([
                        html.H1(children="Select Geography 1:", 
                                style={"fontSize": "18px", 'font-family': 'Gotham Medium', "color": "black", 
                                       "text-align": "left", 'margin-right': '0.5cm','margin-bottom': '0.1cm'}),

                        dcc.Dropdown(
                            id='geo-selection-input1_tab2',
                            searchable = True,
                            clearable = False,
                            value = 'Council District (2023 Boundaries)',
                            options = list(all_options_add_nyc.keys()),
                            style = {"color": 'black',#"#499ED5", 
                                     'fontSize': '16px',
                                     'font-family': 'sans-serif',
                                     'margin-bottom': '0.5cm',
                                    }
                        ),
                    
                    ]),
                        
                    # dynamic header for region dropdown (will change based on geo-selection-input1_tab2, e.g. 'Select a Council District')

                    html.Div([

                        html.Div(
                            id='geo_header1_tab2',
                            style={'margin-bottom': '0.1cm', 'margin-right': '0.5cm'}
                        ),    

                        # dynamic dropdown menu for regions within NYC (will change based on geo-selection-input1_tab2, e.g. listing all council districts)

                        dcc.Dropdown(
                            id='geo-num-selection-input1_tab2',
                            searchable = True,
                            clearable = False,
                            style = {"color": 'black',#"#499ED5", 
                                     'fontSize': '16px',
                                     'font-family': 'sans-serif',
                                     'margin-bottom': '0.5cm',
                                    }
                            )
                        
                    ]), 
    
                    # geography dropdown menu #2

                    html.Div([
                        html.H1(children="Select Geography 2:", 
                                style={"fontSize": "18px", 'font-family': 'Gotham Medium', "color": "black", 
                                       'float': 'left', "text-align": "left", 'margin-bottom':'0.1cm', 
                                       'margin-right': '0.5cm'}),

                        dcc.Dropdown(
                            id='geo-selection-input2_tab2',
                            searchable = True,
                            clearable = False,
                            value = 'New York City',
                            options = list(all_options_add_nyc.keys()),
                            style = {"color": 'black',#"#499ED5", 
                                     'fontSize': '16px',
                                     'font-family': 'sans-serif',
                                     'margin-bottom': '0.5cm',
                                    }
                        ),
                    
                    ]),
                        
                    # dynamic header for region dropdown (will change based on geo-selection-input2_tab2, e.g. 'Select a Council District')

                    html.Div([

                        html.Div(
                            id='geo_header2_tab2',
                            style={'margin-bottom': '0.1cm', 'margin-right': '0.5cm'}
                        ),    

                        # dynamic dropdown menu for regions within NYC (will change based on geo-selection-input1_tab2, e.g. listing all council districts)

                        dcc.Dropdown(
                            id='geo-num-selection-input2_tab2',
                            searchable = True,
                            clearable = False,
                            style = {"color": 'black',#"#499ED5", 
                                     'fontSize': '16px',
                                     'font-family': 'sans-serif',
                                     'margin-bottom': '0.5cm',
                                    }
                            )
                        
                    ]), 
                    
                    # selection for time period 
                        
                    html.Div([                   

                        html.H1(children="Select Time Period:", 
                                style={"fontSize": "18px", 'font-family': 'Gotham Medium', "color": "black", 
                                       'float': 'left', "text-align": "left", 'margin-bottom': '0.1cm', 'margin-right': '0.25cm'}),
                        
                        html.Abbr('\u24D8', id='time-info-tooltip', style={'fontSize':'15px','margin-right': '0.25cm', 'margin-top': '-5px'}), # adding tooltip that will provide info upon hover
                            dbc.Popover(
                                [dbc.PopoverBody(dcc.Markdown(time_markdown_content))],
                                target='time-info-tooltip',
                                trigger='hover',
                                placement='left', 
                                style=popover_style_med
                            ), 
                    ],
                        
                    # placing the header and the info button next to each other 

                    style={
                       'display': 'flex',
                       'flex-direction': 'row',
                       'align-items': 'center',
                      }  
                        
                    ),
    
                    html.Div(
                        dcc.Dropdown(
                            id='time-selection-input_tab2',
                            searchable = True,
                            clearable = False,
                            value = time_periods[-1], # most recent time period
                            options = time_periods,
                            style = {"color": 'black',#"#499ED5", 
                                     'fontSize': '16px',
                                     'font-family': 'sans-serif',
                                     'margin-bottom': '0.5cm',
                                    }
                        ),               

                    ),  
    
                # allowing choice between numbers and percents
    
                html.Div([
                    html.Div(
                        html.H1(children="Select Measure:", 
                                style={"fontSize": "18px", 'font-family': 'Gotham Medium', "color": "black", 
                                       "text-align": "left", 'margin-bottom': '0.1cm', 'margin-right': '0.5cm'}),
                    ),

                    # dynamic dropdown menu for metrics (inputs like 'population' only have number estimates available) 
                    
                    dcc.Dropdown(
                        id='metric-selection-input_tab2',
                        searchable = True,
                        clearable = False,
                        options=['Numbers','Percents'],
                        value='Numbers',
                        style = {"color": 'black',#"#499ED5", 
                                 'fontSize': '16px',
                                 'font-family': 'sans-serif',
                                 'margin-bottom': '0.5cm',
                                }
                        ),
                    
                    ],
                
#                     style={'display':'inline-block','width': '100%'}
                )  
    
        ],
    
        className = 'float-child',
        style={'flex': '1'}, 

    )

#### layout components for tab 3 
    
the_chart = html.Div([ # adding dyanmic chart  
    
           html.Div(
               dcc.Graph(id="the_chart"),
               style={'width': '100%','overflow': 'auto','margin-bottom': '0.2cm'}
           ),
    
           html.Div(
               html.H1(children="Notes: Points shown in grey have poor statistical reliability (CV >= 20). If the error bars on any two points overlap, the difference between these values is not considered statistically significant. When no point appears for a time period, it means that data is not available for the chosen variable in that time period.", 
                    style={"fontSize": "14px", 'font-family':'Gotham Light', 'fontWeight': 'bold', "text-align": "left", 'margin-bottom': '0.5cm'}
                   )
            ),
    ]),

# dropdown menus

chart_dropdowns = html.Div([
        
                # headings for page
        
                html.Div(
                    html.H1(children="VISUALIZE DEMOGRAPHIC TRENDS", 
                            style={"fontSize": "20px", 'font-family': 'Bell Gothic Std Black', 
                                   "color": "black", "text-align": "left", 'margin-bottom': '0.25cm'}),
                    ),
    
                # creating a dropdown menu with demographic variable options 
    
                html.Div([
                    
                    html.H1(children="Select Demographic:", 
                            style={"fontSize": "18px", 'font-family': 'Gotham Medium', "color": "black", 
                                   "text-align": "left", 'margin-right': '0.25cm', 'margin-bottom': '0.1cm'}), 
                    
                    # adding tooltip that will provide info upon hover
                    html.Abbr('\u24D8', id='demo-info-tooltip', style={'fontSize':'15px', 'margin-right': '0.25cm', 'margin-top':'-5px'}), 
                        dbc.Popover(
                            [dbc.PopoverBody(dcc.Markdown(demo_markdown_content))],
                            target='demo-info-tooltip',
                            trigger='hover',
                            placement='left', 
                            style=popover_style_med
                        ),
                
                    ],

                    # putting the button and the header next to each other

                    style={
                        'display': 'flex',
                        'flex-direction': 'row',
                        'align-items': 'center',
                        }

                    ),
                    
                    html.Div(
                        dmc.Select(
                            placeholder='Select...',
                            id='demo-selection-input_tab3', # name of the selected inputs from the demo dropdown
                            searchable = True,
                            clearable = False,
                            value='Total population: Data Profiles 5-Year', # starting value is Total population 
                            data=no_income_dropdown_dict, # excluding income variables due to inflation preventing comparison over time
                            style={'font-family':'sans-serif', 'fontSize': '16px', 'margin-bottom': '0.55cm'}
                        )
                        
                    ),

                # geography dropdown menu 

                html.Div([
                    html.H1(children="Select Geography:", 
                            style={"fontSize": "18px", 'font-family': 'Gotham Medium', "color": "black", 
                                   "text-align": "left", 'margin-bottom': '0.1cm', 'margin-right': '0.5cm'}),

                    dcc.Dropdown(
                        id='geo-selection-input_tab3',
                        searchable = True,
                        clearable = False,
                        value = 'Council District (2023 Boundaries)',
                        options = list(all_options_add_nyc.keys()),
                        style = {"color": 'black',#"#499ED5", 
                                 'fontSize': '16px',
                                 'font-family': 'sans-serif',
                                 'margin-bottom': '0.55cm',
                                }
                        )
                    
                ]),
    
                # dynamic header for region dropdown (will change based on geo-selection-input_tab3, e.g. 'Select a Council District')

                html.Div([

                    html.Div(
                        id='geo_header_tab3',
                        style={'margin-bottom':'0.1cm', 'margin-right': '0.5cm'},
                    ), 

                    # dynamic dropdown menu for regions within NYC (will change based on geo-selection-input_tab3, e.g. listing all council districts)  

                    dcc.Dropdown(
                        id='geo-num-selection-input_tab3',
                        searchable = True,
                        clearable = False,
                        style = {"color": 'black',#"#499ED5", 
                                 'fontSize': '16px',
                                 'font-family': 'sans-serif',
                                 'margin-bottom': '0.55cm',
                                }
                        )
                    
                ]),

                # allowing choice of time period
    
                html.Div([
                    
                 html.H1(children="Select Time Periods:", 
                            style={"fontSize": "18px", 'font-family': 'Gotham Medium', "color": "black", 
                                "text-align": "left", 'margin-bottom': '0.1cm', 'margin-right': '0.25cm'}),

                    html.Abbr('\u24D8', id='time-info-tooltip', style={'fontSize':'15px', 'margin-right':'0.25','margin-top':'-5px'}), # adding tooltip that will provide info upon hover
                        dbc.Popover(
                            [dbc.PopoverBody(dcc.Markdown(time_markdown_content))],
                            target='time-info-tooltip',
                            trigger='hover',
                            placement='left', 
                            style=popover_style_med
                        ),
                                        
                    ],

                    # putting the button and the header next to each other

                    style={
                        'display': 'flex',
                        'flex-direction': 'row',
                        'align-items': 'center',
                        }

                    ),
                    
                    html.Div(
                        dcc.Dropdown(
                            id='time-selection-input_tab3',
                            searchable = True,
                            clearable = False,
                            multi=True,
                            value = time_periods,
                            options = time_periods,
                            style = {"color": 'black',#"#499ED5", 
                                     'fontSize': '16px',
                                     'font-family': 'sans-serif',
                                     'margin-bottom': '0.55cm',
                                    }
                        )
                    ),
    
                # allowing choice between numbers and percents
                
                html.Div([
                    html.H1(children="Select Measure:", 
                            style={"fontSize": "18px", 'font-family': 'Gotham Medium', "color": "black", 
                                   "text-align": "left", 'margin-bottom': '0.1cm', 'margin-right': '0.5cm'}),

                # dynamic dropdown menu for metrics (demo inputs like 'total population' only have number estimates available)     
                #                
                dcc.Dropdown(
                    id='metric-selection-input_tab3',
                    searchable = True,
                    clearable = False,
                    # options=['Numbers','Percents'],
                    # value='Numbers',
                    style = {"color": 'black',#"#499ED5", 
                             'fontSize': '16px',
                             'font-family': 'sans-serif',
                             'margin-bottom': '1cm',
                            }
                    ), 

                ],
                
#                 style={'display':'inline-block','width': '100%'} 
                    
                ),
    
        ],

        className = 'float-child',
        style={'flex': '1'}, 
    )

#### layout components for tab 4 

about_page_text = html.Div([
    
                    html.Div(
                        html.H1(children="ABOUT COUNCILCOUNT", 
                                style={"fontSize": "30px", 'font-family': 'Gotham Medium', "color": "black", "text-align": "left", 'margin-bottom': '0.35cm'}),
                        ),
    
                    html.Div([
                        html.H1(children="How to Use CouncilCount", 
                                style={"fontSize": "24px", 'font-family': 'Gotham Medium', "color": "black", "text-align": "left", 'margin-bottom': '0.25cm'}),

                        dcc.Markdown(how_to_markdown_content, style={"fontSize": "16px", 'margin-bottom': '0.5cm'})

                        ]),
    
                    html.Div([
                        html.H1(children="Map View", 
                                style={"fontSize": "18px", 'font-family': 'Gotham Medium', "color": "black", "text-align": "left", 'margin-bottom': '0.25cm'}),
                        
                        dcc.Markdown(map_view_markdown_content, style={"fontSize": "16px", 'margin-bottom': '0.5cm'})

                        ]),
    
                    html.Div([
                        html.H1(children="Table View", 
                                style={"fontSize": "18px", 'font-family': 'Gotham Medium', "color": "black", "text-align": "left", 'margin-bottom': '0.25cm'}),

                        dcc.Markdown(table_view_markdown_content, style={"fontSize": "16px", 'margin-bottom': '0.5cm'})

                        ]),
    
                    html.Div([
                        html.H1(children="Chart View", 
                                style={"fontSize": "18px", 'font-family': 'Gotham Medium', "color": "black", "text-align": "left", 'margin-bottom': '0.25cm'}),

                        dcc.Markdown(chart_view_markdown_content, style={"fontSize": "16px", 'margin-bottom': '0.5cm'}),

                        dcc.Markdown("""*""" + data_reliability_note + """*""", style={"fontSize": "14px", 'margin-bottom': '0.5cm'})
                        
                        ]),
    
                    html.Div([
                        html.H1(children="Background on Demographic Estimates", 
                                style={"fontSize": "24px", 'font-family': 'Gotham Medium', "color": "black", "text-align": "left", 'margin-bottom': '0.25cm'}),

                        dcc.Markdown(background_markdown_content, style={"fontSize": "16px", 'margin-bottom': '0.5cm'})

                        ]),
    
                    html.Div([
                        html.H1(children="Notes on Demographic Variables", 
                                style={"fontSize": "24px", 'font-family': 'Gotham Medium', "color": "black", "text-align": "left", 'margin-bottom': '0.25cm'}),

                        dcc.Markdown(variable_markdown_content, style={"fontSize": "16px", 'margin-bottom': '0.5cm'})

                        ]),
    
                    html.Div([
                        html.H1(children="Data Reliability", 
                                style={"fontSize": "24px", 'font-family': 'Gotham Medium', "color": "black", "text-align": "left", 'margin-bottom': '0.25cm'}),

                        dcc.Markdown(data_reliability_markdown_content, style={"fontSize": "16px", 'margin-bottom': '0.5cm'})

                        ]),

                    html.Div([
                        html.H1(children="CouncilCount Geographies", 
                                style={"fontSize": "24px", 'font-family': 'Gotham Medium', "color": "black", "text-align": "left", 'margin-bottom': '0.25cm'}),

        
                        dcc.Markdown("""*""" + geo_marker_content_note + """*""", style={"fontSize": "14px", 'margin-bottom': '0.5cm'}),
                        
                        dcc.Markdown(geo_markdown_content, style={"fontSize": "16px", 'margin-bottom': '1cm'})

                        ]),
    
                    html.Div(
                        dcc.Markdown("""*""" + contact_markdown_content + """*""", style={"fontSize": "14px", 'margin-bottom': '0.5cm'})
                    )
    
    
        ])




# %%
# building the three tabs' layouts in dbc columns and rows
# responsive to changes in window size

map_layout = [  # tab 1
    dbc.Container([
        dbc.Row(
            [
                dbc.Col(
                    the_map,
                    style={'padding-left': '20px', 'padding-right': '20px'},
                    xs=dict(order='first', size=10), 
                    lg=dict(order='first', size=7), 
                ),
                dbc.Col(
                    map_dropdowns,
                    style={'padding-left': '20px', 'padding-right': '20px'},
                    xs=dict(order='last', size=10),
                    lg=dict(order='last', size=4), 
                ),
            ],
            justify='center'
        ),

        dbc.Row(
            [
                dbc.Col(
                    the_regional_table,
                    style={'padding-left': '20px', 'padding-right': '20px'},
                    xs=dict(order='first', size=10), 
                    lg=dict(order='first', size=7),  
                ),
                # using a blank column to match the previous row's spacing (so bottom and top row align)
                dbc.Col( 
                    '',
                    style={'padding-left': '20px', 'padding-right': '20px'},
                    xs=dict(order='last', size=10),  
                    lg=dict(order='last', size=4),   
                ),
            ],
            justify='center' 
        ),
    ], fluid=True)
]


table_layout = [ # tab 2
    
    dbc.Container([
    
        dbc.Row([
            dbc.Col(
                the_table,
                style={'padding-left':'20px', 'padding-right':'20px', 'padding-top':'5px'},
                xs=dict(order='first', size=11),
                sm=dict(order='first', size=10),
                lg=dict(order='first', size=8),
                xl=dict(order='first', size=7)
            ),
            dbc.Col(
                table_dropdowns,
                style={'padding-left':'20px', 'padding-right':'20px', 'padding-top':'5px'},
                xs=dict(order='last', size=11),
                sm=dict(order='last', size=10),
                lg=dict(order='last', size=4),
                xl=dict(order='last', size=4)
            ),
        ],

        justify='center'

        ),
        
    ],
        
    fluid=True 
    
    )
        
    ]

chart_layout = [ # tab 3
    
    dbc.Container(
    
        dbc.Row([
            dbc.Col(
                the_chart,
                style={'padding-left':'20px', 'padding-right':'20px'},
                xs=dict(order='first', size=10),
                lg=dict(order='first', size=7),
            ),
            dbc.Col(
                chart_dropdowns,
                style={'padding-left':'20px', 'padding-right':'20px'},
                xs=dict(order='first', size=10),
                lg=dict(order='last', size=4),
            ),
        ],

        justify='center'

        ),
        
        fluid=True
        
      )
    
    ]

about_layout = [ # tab 4
    
    dbc.Container(
        
        dbc.Row([
            dbc.Col(
                about_page_text,
                style={'padding-left':'20px', 'padding-right':'20px', 'padding-top':'5px'},
                xs=dict(size=10),
                lg=dict(size=9)
            ), 
        ],
        
        justify='center'
            
        ),
        
        fluid=True 
    )
    
    ]


# %%
# putting everything together in app.layout

# tab style

tab_style = {'font-size': '14px', 'background': 'white', 'font-family': 'Gotham Medium', 
             'text-align': 'left', 'border-color':'white', 'padding':'3px', 'width':'5cm', 
             "display": "inline-block"}

selected_tab_style = {'fontWeight':'bold', 'font-size': '14px', 'background': 'white', 
                      'font-family': 'Gotham Medium', 'text-align': 'left', 'border-color':'white', 
                      'padding':'3px', 'width':'5cm', "display": "inline-block"}

app.layout = html.Div([
    
                    dbc.Row([ # header elements that are consistent across all tabs
                        dbc.Col(
                            header_top_1,
                            xs=dict(order=1, size=9, offset=1)
                        ),
                        
                        dbc.Col(
                            header_top_2,
                            xs=dict(order=2, size=1, offset=1)
                        ),

                    ],

                    align="center",    
                    justify='start'

                    ),
    
                   dbc.Row( # header elements that are consistent across all tabs
                       dbc.Col(
                           header_bottom,
                           xs=dict(order=1, size=10, offset=1)
                       ),
                    
                    ),
                    
                   dbc.Row( # tabs that establish app view
                       dbc.Col(
                           dcc.Tabs(
                               id='tabs',
                               value='tab-1',
                               children=[
                                   dcc.Tab(label='MAP VIEW', value='tab-1', style=tab_style, selected_style = selected_tab_style),
                                   dcc.Tab(label='TABLE VIEW', value='tab-2', style=tab_style, selected_style = selected_tab_style),
                                   dcc.Tab(label='CHART VIEW', value='tab-3', style=tab_style, selected_style = selected_tab_style),
                                   dcc.Tab(label='ABOUT', value='tab-4', style=tab_style, selected_style = selected_tab_style)
                                ],

                               style={'margin-bottom': '0.75cm'}

                           ),

                           xs=dict(size=11, offset=1),
                           lg=dict(size=11, offset=1), 
                       ),
                   ),  
                       
                    html.Div(id='tabs-content'), # dyanmic html.Div that changes based on selected tab
                ])


# %%
# programming the interactive elements of the app

geo_dict = {'Council District (2013 Boundaries)': 'councildist_2013', # to convert displayed names to values used in the geo_df
            'Council District (2023 Boundaries)': 'councildist_2023',
            'Community District': 'communitydist',
            'School District': 'schooldist',
            'Police Precinct': 'policeprct',
            'Modified ZIP Code Tabulation Area': 'modzcta',
            'Neighborhood Tabulation Area': 'nta',
            'Borough': 'borough',
            'New York City': 'city'}

@app.callback( # callback that changes layout view based on selected tab
    Output('tabs-content', 'children'), # displayed content
    [Input('tabs', 'value')], # selected tab
)
                    
def render_tab(tab):

    if tab == 'tab-1':
        return map_layout
    elif tab == 'tab-2':
        return table_layout
    elif tab == 'tab-3':
        return chart_layout
    elif tab == 'tab-4':
        return about_layout
    
######################## # tab 1 

@app.callback( # callback that establishes 'geo-num-selection-input_tab1' dropdown menu options based on geography chosen
    [Output('geo-num-selection-input_tab1', 'options'), # dropdown menu options
     Output('geo_header_tab1', 'children')], # header for dropdown menu
    [Input('geo-selection-input_tab1', 'value')] # geo region chosen
)

def set_geo_num_options_tab1(selected_geo): 
    
    if 'Council District' in selected_geo: selected_geo_name = 'Council District' # not including "(2023 Boundaries)" in header
    elif 'ZIP Code' in selected_geo: selected_geo_name = 'MODZCTA' # abbreviation in header
    elif 'Neighborhood Tabulation Area' in selected_geo: selected_geo_name = 'NTA' # abbreviation in header
    else: selected_geo_name = selected_geo

    options = [{'label': 'Select All', 'value': 'all'}]  # Add Select All option
    options += [{'label': i, 'value': i} for i in all_options[selected_geo]]
    header = [html.H1('Select ' + selected_geo_name + 's to Compare:', style={'fontSize': '18px',
                                                                               'font-family': 'Gotham Medium',
                                                                               'color': 'black',
                                                                               'text-align': 'left',
                                                                               'margin-bottom': '0.1cm'})]

    return options, header

@app.callback( # callback that sets the default value for the geo_num dropdown based on which set of dropdown options is triggered in previous callback
    Output('geo-num-selection-input_tab1', 'value'), # default value for geo_num
    Input('geo-num-selection-input_tab1', 'options'), # list of options for geo_num
    prevent_initial_callback=True
)

def set_geo_num_value_tab1(available_options):
    
    return [available_options[1]['value'], available_options[2]['value']]

@app.callback( # callback that establishes 'metric-selection-input_tab1' dropdown menu options based on demographic chosen
    Output('metric-selection-input_tab1', 'options'), # dropdown menu options
    Input('demo-selection-input_tab1', 'value') # demo chosen
)

def set_metric_options_tab1(selected_demo): 

    if (selected_demo in [None, []]): # prevent update if demo variable isn't selected
        raise PreventUpdate
        return

    # only number estimates are available
    if selected_demo in ['Total population: Data Profiles 5-Year', 'Total households Data Profiles 5-Year']: 
        options = ['Numbers']
    # only percent estimates are available
    elif selected_demo in ['Unemployment rate']: 
        options = ['Percents']
    else: # both available
        options = ['Numbers', 'Percents']

    return options

@app.callback( # callback that sets the default value for the metric dropdown based on which set of dropdown options is triggered in previous callback
    Output('metric-selection-input_tab1', 'value'), # default value for geo_num
    Input('metric-selection-input_tab1', 'options'), # list of options for geo_num
    prevent_initial_callback=True
)

def set_metric_value_tab1(available_options):
    
    return available_options[0]

@app.callback( # callback for downloading data table as excel upon click (based on selected geography, time)
    Output('download-dataframe-excel', 'data'), # excel file
    Input('btn_excel', 'n_clicks'), # click on button
    State('time-selection-input_tab1', 'value'), # time period chosen
    State('geo-selection-input_tab1', 'value'), # geographic region chosen
    prevent_initial_call=True
)

def download_geo_df(n_clicks, time, geo_value): # setting which df will be downloaded based on selected geo and time period 
   
    geo = geo_dict[geo_value] # geography selected by user (e.g. 'Council District (2023 Boundaries)') - using geo_dict to convert displayed name to name used in geo_df ('council23')
    year = time[-4:]
    
    data_dictionary = globals()[f'data_dictionary_{year}']
    
    if geo in ['communitydist', 'nta', 'policeprct', 'modzcta']:
        geo_df = globals()[f'{geo}_geographies_{year}_all_regions'] # including regions not displayed on map
    else: 
        geo_df = globals()[f'{geo}_geographies_{year}'] 
        
    output_filename = f'demo-estimates_by-{geo}_{year}-ACS5Year.xlsx'
    
    with pd.ExcelWriter(output_filename) as writer:
        # write each DataFrame to a different sheet
        geo_df.drop(columns='geometry', errors='ignore').to_excel(writer, sheet_name='Demographic Estimates', index=False)
        data_dictionary.to_excel(writer, sheet_name='Data Dictionary', index=False)

    # send the created Excel file back to the user
    return dcc.send_file(output_filename)

@app.callback( # callback for updating the page based on all selected values
    [Output('the_map', 'srcDoc'), # outputs graph -> folium version
    Output('map_tableDiv', 'children')], # outputs table
    [Input('demo-selection-input_tab1', 'value'), # demographic variable dropdown selection
    Input('geo-selection-input_tab1', 'value'), # geography dropdown selection
    Input('geo-num-selection-input_tab1', 'value'), # geographic region dropdown selection
    Input('metric-selection-input_tab1', 'value'), # metric chosen
    Input('time-selection-input_tab1', 'value'), # time period chosen 
    Input('rank-selection-input_tab1', 'value')], # choice about ranking table
    prevent_initial_call=True
)

def update_output_tab1(demo_value, geo_value, geo_num_values, metric, time, rank_choice): # based on user's selections in the dropdown menus, choropleth map and data table will update
    
    if (demo_value in [None, []]): # prevent update if demo variable isn't selected
        raise PreventUpdate
        return
    
    selected_demo = demo_value
    
    # preparing variables 
    
    geo = geo_dict[geo_value] # geography selected by user (e.g. 'Council District (2023 Boundaries)') - using geo_dict to convert displayed name to name used in geo_df ('council23')
    
    # geo_num -> geographic regions selected by user (e.g. ['1','2'] for council districts 1 and 2)
    if 'all' in geo_num_values: geo_num = all_options[geo_value] # when Select All is chosen, input list of all values for this geo
    else: geo_num = geo_num_values 
    
    year = int(time[-4:]) # setting year based on time period
    
    name_to_code_dict = deepcopy(globals()[f'name_to_code_dict_{year}']) # used to convert user-facing names to var_codes
    name_to_denom_dict = deepcopy(globals()[f'name_to_denom_dict_{year}']) # used to access denominator info

    # setting DFs based on selected geography and year 
    
    geo_df = deepcopy(globals()[f'{geo}_geographies_{year}'])
    nyc_wide_df = deepcopy(globals()[f'nyc_wide_estimates_{year}'])
            
    # creating new map
        
    fig = folium_plot(selected_demo, geo, geo_df, metric, name_to_code_dict, name_to_denom_dict)
                
    # preparing table
    
    # need conversion dict for NTA names
    if geo == 'nta': conversion_dict = nta_dict
    else: conversion_dict = None

    # rank choice for comparison table
    rank = rank_choice
    # if rank_choice == None: rank = None
    # elif rank_choice == 'Rank low to high': rank = False
    # elif rank_choice == 'Rank high to low': rank = True

    mycolumns, table_label, table_tab1 = get_table_tab1(geo, geo_num, geo_df, nyc_wide_df, selected_demo, metric, name_to_code_dict, conversion_dict, rank)

    # update table
    table = html.Div([html.Label(table_label, style={'font-family': 'Gotham Medium',
                                                     'fontWeight':'normal',
                                                     'fontSize': '16px',
                                                     'margin-bottom': '0.15cm'}), 
                    dash_table.DataTable(
#                         id='table_tab1',
                        columns= mycolumns,
                        data=table_tab1.to_dict("records"),
                        merge_duplicate_headers=True,
                        export_format='csv',#'xlsx',
                        export_headers='display',
                        page_size=10,
                        page_action='native',
                        css=[{'selector':'.export','rule':'position:absolute;left:0px;bottom:-37px;background:#F8F8F8'}],
                        style_cell={'fontSize': '12px','textAlign':'center', 'font-family': 'Gotham Medium', 'backgroundColor': '#F8F8F8'},
                        style_data={'color': 'black', 'font-family': 'Gotham Light', 'backgroundColor': 'white', 'fontWeight':'bold'},
                        style_header={'fontSize': '15px'},
                        style_data_conditional=[ # styling the column with variable names grey to match headers
                                {
                                    'if': {
                                        'column_id': mycolumns[0]['id'],
                                    },
                                    'backgroundColor': '#F8F8F8',
                                    'font-family': 'Gotham Medium',
                                    
                                },
                            
                        ]
                    )
                      
                ])
    
    return open(fig, 'r').read(), table # return updated map and table

@app.callback(
    Output('reliability_text_tab1', 'children'), # text for pop-up that occurs when data in table is unreliable
    [Input('map_tableDiv', 'children'), # table from previous function
    Input('demo-selection-input_tab1', 'value'), # demographic variable dropdown selection
    # Input('geo-selection-input_tab1', 'value'), # geography dropdown selection
    Input('geo-num-selection-input_tab1', 'value')], # geographic region dropdown selection
    prevent_initial_call=True
)

def output_rel_info(nyc_table, demo_value, geo_num_values):
    
    if (demo_value in [None, []]): 
        raise PreventUpdate
        return
    
    rel_list = []
    
    # setting number of rows to loop through
    if 'all' in geo_num_values: length = len(nyc_table['props']['children'][1]['props']['data']) # will include all rows
    else: length = len(geo_num_values) + 1 # only includes the individual rows selected
    
    for i in range(0,length): # cycling through all rows of the table to collect values
        row = nyc_table['props']['children'][1]['props']['data'][i]
        rel_list.append(str(row['Estimate'])) # accessing demographic value for each chosen region
        
    rel_list = ''.join(rel_list) # converting to string
        
    if '*' in rel_list: # if poor reliability marker has been added to an NYC-wide or region-specific value
        text = "*poor statistical reliability" # add message
    else:
        text = "" # otherwise add no message
    
    return text

######################## # tab 2 

@app.callback( # callback that establishes 'geo-num-selection-input1_tab2' dropdown menu options based on geography chosen
    [Output('geo-num-selection-input1_tab2', 'options'), # options for dropdown
     Output('geo_header1_tab2', 'children')], # header for dropdown
    [Input('geo-selection-input1_tab2', 'value')], # geo region chosen
)

def set_geo_num_options1_tab2(selected_geo): 
            
    if selected_geo == 'New York City': selected_geo_name = 'Region' # for header when NYC is selected as geography
    elif 'Council District' in selected_geo: selected_geo_name = 'Council District' # not including "(2023 Boundaries)" in header
    else: selected_geo_name = selected_geo
        
    return [{'label': i, 'value': i} for i in all_options_add_nyc[selected_geo]], [html.H1('Select ' + selected_geo_name + ':', style={'fontSize': '18px',
                                                                                                                               'font-family': 'Gotham Medium',
                                                                                                                               'color': 'black',
                                                                                                                               'text-align': 'left',
                                                                                                                               'margin-bottom':'0.1cm'})]

@app.callback( # callback that sets the default value for the geo_num dropdown based on which set of dropdown options is triggered in previous callback
    Output('geo-num-selection-input1_tab2', 'value'),
    Input('geo-num-selection-input1_tab2', 'options'),
    prevent_initial_callback = True
)

def set_geo_num_value1_tab2(available_options):
    
    return available_options[0]['value']

@app.callback( # callback that establishes 'geo-num-selection-input' dropdown menu options based on geography chosen
    [Output('geo-num-selection-input2_tab2', 'options'), # options for dropdown
     Output('geo_header2_tab2', 'children')], # header for dropdown
    [Input('geo-selection-input2_tab2', 'value')], # geo region chosen
)

def set_geo_num_options2_tab2(selected_geo): 
            
    if selected_geo == 'New York City': selected_geo_name = 'Region' # for header when NYC is selected as geography
    elif 'Council District' in selected_geo: selected_geo_name = 'Council District' # not including "(2023 Boundaries)" in header
    else: selected_geo_name = selected_geo
        
    return [{'label': i, 'value': i} for i in all_options_add_nyc[selected_geo]], [html.H1('Select ' + selected_geo_name + ':', style={'fontSize': '18px',
                                                                                                                               'font-family': 'Gotham Medium',
                                                                                                                               'color': 'black',
                                                                                                                               'text-align': 'left',
                                                                                                                               'margin-bottom':'0.1cm'})]

@app.callback( # callback that sets the default value for the geo_num dropdown based on which set of dropdown options is triggered in previous callback
    Output('geo-num-selection-input2_tab2', 'value'), # default value for geo_num
    Input('geo-num-selection-input2_tab2', 'options'), # list of options for geo_num
    prevent_initial_call=True
)

def set_geo_num_value2_tab2(available_options):
    
    return available_options[0]['value']

@app.callback( # callback for updating the page based on all selected values
    [Output('table_tableDiv', 'children'), # outputs table as a dash_table
     Output('table_label','children'), # table title
     Output('reliability_text_tab2', 'children')], # reliability message
    [Input('group-selection-input', 'value'), # demographic variable dropdown selection
    Input('geo-selection-input1_tab2', 'value'), # geography dropdown selection 1
    Input('geo-num-selection-input1_tab2', 'value'), # geographic region dropdown selection 1
    Input('geo-selection-input2_tab2', 'value'), # geography dropdown selection 2
    Input('geo-num-selection-input2_tab2', 'value'), # geographic region dropdown selection 2
    Input('time-selection-input_tab2', 'value'), # time period selection
    Input('metric-selection-input_tab2', 'value'), # metric chosen (numbers or percents) 
    Input('rel-check-box','value')], # whether user chooses to see reliability data or not
    prevent_initial_call=True
)

def update_output_tab2(group_values, geo_value1, geo_num_value1, geo_value2, geo_num_value2, time, metric, rel_info): # based on user's selections in the dropdown menus, choropleth map and data table will update
    
    if (group_values in [None, []]) or ((geo_value1 == geo_value2) & (geo_num_value1 == geo_num_value2)): # prevent update if group variable isn't selected or selected_regions are the same
        raise PreventUpdate
        return
    
    # setting variables

    # groups selected by user
    selected_groups = group_values
    # geography selected by user (e.g. 'Council District (2023 Boundaries)')
    # using geo_dict to convert displayed name to name used in in geo_df ('councildist_2023')
    geo1 = geo_dict[geo_value1] 
    geo2 = geo_dict[geo_value2]
    # geographic region selected by user (e.g. 1 for Council District 1)
    geo_num1 = geo_num_value1 
    geo_num2 = geo_num_value2 
    
    var_dict = dropdown_dict
    
    if rel_info == ['check-yes']: # user selection for whether or not relaibility data should be shown
        rel_info = True
        rel_message = '*poor statistical reliability'
    else:
        rel_info = False
        rel_message = ''
    
    # preparing table
    
    year = int(time[-4:]) # whatever individual time period was selected by user
    
    # used to convert user-facing names to var_codes
    name_to_code_dict = deepcopy(globals()[f'name_to_code_dict_{year}']) 

    # DFs for `get_table_tab2()`` function

    for num, geo in [(1, geo1),(2, geo2)]: 
        if geo == 'city':
            # determined based on selected geo and year(s)
            globals()[f'geo_df{num}'] = deepcopy(globals()[f'nyc_wide_estimates_{year}']) 
        else:
            # determined based on selected geo and year(s)
            globals()[f'geo_df{num}'] = deepcopy(globals()[f'{geo}_geographies_{year}']) 

    # preparing table
    
    # need conversion dict for NTA names
    if 'nta' in [geo1, geo2]: conversion_dict = nta_dict
    else: conversion_dict = None
    
    # creating table
    table_label, table_tab2 = get_table_tab2(geo1, geo_num1, geo_df1, geo2, geo_num2, geo_df2, selected_groups, metric, name_to_code_dict, dropdown_dict, conversion_dict, rel_info) 
    # converting to Dash usable format 
    mycolumns, table_for_dash = convert_df_to_dash(table_tab2)  
    
    # adding reliability message if unreliable estimates in the data
    list_of_values = []
    # searching table for '*' to determine message
    for i in list(range(0, len(table_for_dash))): 
        for value in list(table_for_dash[i].values()): 
            value = str(value)
            list_of_values.append(value)
        if '*' in ''.join(list_of_values):
            rel_message = '*poor statistical reliability'
        else:
            rel_message = ''  
    
    # update table

    dashtable = html.Div( 
                      
                    dash_table.DataTable(
#                         id='table_tab2',
                        columns=mycolumns,
                        data=table_for_dash,
                        merge_duplicate_headers=True,
                        export_format='csv',#'xlsx',
                        export_headers='display',
                        page_size=20,
                        css=[{'selector':'.export','rule':'position:absolute;left:0px;bottom:-37px;background:#F8F8F8'}],
                        style_table={'minWidth': '100%', 'overflowX': 'scroll', 'overflowY': 'scroll', 'border':'0.75px solid #C0C0C0'},
                        style_cell={'fontSize': '12px','textAlign':'center'},
                        style_header={'fontSize': '15px', 'font-family': 'Gotham Medium', 'backgroundColor': '#F8F8F8'},
                        style_data={'color': 'black', 'font-family': 'Gotham Light', 'backgroundColor': 'white', 'fontWeight':'bold'},
                        style_header_conditional=[ # removing line between empty cells 
                                {
                                    'if': {
                                        'column_id': mycolumns[0]['id'],
                                    },
                                    'border-top':'None',
                                },
                            
                            ],
                        
                        style_data_conditional=[ # styling the column with variable names grey to match headers
                                {
                                    'if': {
                                        'column_id': mycolumns[0]['id'],
                                    },
                                    'backgroundColor': '#F8F8F8',
                                    'font-family': 'Gotham Medium',
                                    'textAlign':'right',
                                    'padding-right':'5px',
                                },

                            ],
                    ),
                    # add a bottom margin to the wrapping html.Div
                    className="mb-5" 
                )
    
    label = [html.H1(table_label, style={'font-family': 'Gotham Medium',
                                         'fontWeight':'normal',
                                         'fontSize': '16px',
                                         })]
    
    return dashtable, label, rel_message

######################## # tab 3

@app.callback( # callback that establishes 'geo-num-selection-input_tab3' dropdown menu options based on geography chosen
    [Output('geo-num-selection-input_tab3', 'options'), # dropdown options
     Output('geo_header_tab3', 'children')], # header for dropdown menu
    [Input('geo-selection-input_tab3', 'value')] # geo region chosen
)

def set_geo_num_options_tab3(selected_geo): 
    
    # for header when NYC is selected as geography     
    if selected_geo == 'New York City': selected_geo_name = 'Region' 
    # not including "(2023 Boundaries)" in header
    elif 'Council District' in selected_geo: selected_geo_name = 'Council District' 
    else: selected_geo_name = selected_geo
        
    return [{'label': i, 'value': i} for i in all_options_add_nyc[selected_geo]], [html.H1('Select ' + selected_geo_name + 's:', style={'fontSize': '18px',
                                                                                                                               'font-family': 'Gotham Medium',
                                                                                                                               'color': 'black',
                                                                                                                               'text-align': 'left',
                                                                                                                               'margin-bottom':'0.1cm'})]

@app.callback( # callback that sets the default value for the geo_num dropdown based on which set of dropdown options is triggered in previous callback
    Output('geo-num-selection-input_tab3', 'value'), # default value for geo_num
    Input('geo-num-selection-input_tab3', 'options'), # list of options for geo_num
    prevent_initial_call=True
   
)

def set_geo_num_value_tab3(available_options):
    
    return available_options[0]['value']

@app.callback( # callback that establishes 'metric-selection-input_tab3' dropdown menu options based on demographic chosen
    Output('metric-selection-input_tab3', 'options'), # dropdown menu options
    Input('demo-selection-input_tab3', 'value') # demo chosen
)

def set_metric_options_tab3(selected_demo): 

    if (selected_demo in [None, []]): # prevent update if demo variable isn't selected
        raise PreventUpdate
        return

    # only number estimates are available
    if selected_demo in ['Total population: Data Profiles 5-Year', 'Total households: Data Profiles 5-Year']:
        options = ['Numbers']
    # only percent estimates are available
    elif selected_demo in ['Unemployment rate']: 
        options = ['Percents']
    else: # both available
        options = ['Numbers', 'Percents']

    return options

@app.callback( # callback that sets the default value for the metric dropdown based on which set of dropdown options is triggered in previous callback
    Output('metric-selection-input_tab3', 'value'), # default value for geo_num
    Input('metric-selection-input_tab3', 'options'), # list of options for geo_num
    prevent_initial_callback=True
)

def set_metric_value_tab3(available_options):
    
    return available_options[0]

@app.callback(
    Output("the_chart", "figure"), # chart
    [Input('demo-selection-input_tab3', 'value'), # demographic variable dropdown selection
    Input('geo-selection-input_tab3', 'value'), # geography dropdown selection
    Input('geo-num-selection-input_tab3', 'value'), # geographic region dropdown selection
    Input('metric-selection-input_tab3', 'value'), # measure chosen (Percents/ Numbers)
    Input('time-selection-input_tab3', 'value')], # time period chosen 
    prevent_initial_call=True
)


def update_output_tab3(demo_value, geo_value, geo_num_value, metric, time):
    
    # prevent update if demo variable isn't selected, fewer than two time periods selected
    if (demo_value in [None, []]) or (len(time) < 2): 
        raise PreventUpdate
        return
    
    # setting variables
    
    selected_demo = demo_value
    # geography selected by user (e.g. 'Council District (2023 Boundaries)') - using geo_dict to convert displayed name to name used in geo_df ('councildist_2023')
    geo = geo_dict[geo_value] 
    geo_num = geo_num_value
    
    # always have years in chronological order
    years = sorted([int(t[-4:]) for t in time])
    # should be the most recent year, because that won't have any missing variables 
    name_to_denom_dict = globals()[f'name_to_denom_dict_{years[-1]}'] 

    # list for `make_line_chart()` function
    geo_dfs = [] 
    name_to_code_dicts = []
        
    # number of loops based on number of years selected
    for num in list(range(1,len(years)+1)): 
        if geo == 'city':
            # determined based on selected geo and year(s)
            globals()[f'geo_df{num}'] = deepcopy(globals()[f'nyc_wide_estimates_{years[num-1]}']) 
        else:
            globals()[f'geo_df{num}'] = deepcopy(globals()[f'{geo}_geographies_{years[num-1]}']) 
        # adding to list
        geo_dfs.append(globals()[f'geo_df{num}']) 
        
        # used to convert user-facing names to var_codes
        globals()[f'name_to_code_dict{num}'] = deepcopy(globals()[f'name_to_code_dict_{years[num-1]}']) 
        # adding to list
        name_to_code_dicts.append(globals()[f'name_to_code_dict{num}']) 
                
    # need conversion dict for NTA names
    if geo == 'nta': conversion_dict = nta_dict
    else: conversion_dict = None
    
    fig = make_line_chart(selected_demo, geo, geo_num, geo_dfs, years, metric, name_to_code_dicts, name_to_denom_dict, conversion_dict)

    return fig

# %%
# # comment out when using docker
# if __name__ == "__main__":
#     app.run_server(port = 8056) # to run locally
#     #app.run_server(host = '192.168.254.112', port = 8000) # uncomment when putting this up on the server

# %%
# uncomment for docker 

if __name__ == "__main__":
    # create the argument parser
    parser = argparse.ArgumentParser(description="Specify the environment and server settings.")

    # create a mutually exclusive group for docker, server, and local (local is default)
    group = parser.add_mutually_exclusive_group()
    
    # add flags for docker and server (local is default)
    group.add_argument('--local', action='store_true', help='Run the app locally')
    group.add_argument('--docker', action='store_true', help='Run the app via a Docker container with default Docker settings')
    group.add_argument('--server', action='store_true', help='Run the app on the server with default server settings')

    # add optional flags for host and port (only allowed for local)
    parser.add_argument('--host', type=str, help='Host address to run the app on (only for local)')
    parser.add_argument('--port', type=int, help='Port to run the app on (only for local)')

    # parse the arguments
    args = parser.parse_args()

    # check if the user is trying to specify custom host/port with --docker or --server
    if (args.docker or args.server) and (args.host or args.port):
        print("Error: You cannot specify custom host or port when running via Docker or on the server.", file=sys.stderr)
        sys.exit(1)

    # set default values for each environment
    if args.docker:
        host = '0.0.0.0'
        port = 8056
        environment = "Docker"
    elif args.server:
        host = '192.168.254.112'
        port = 8000
        environment = "Server"
    else:
        # default to local environment
        host = args.host if args.host else '127.0.0.1'
        port = args.port if args.port else 8056
        environment = "Local"
    
    # output the chosen settings
    print(f"Running in {environment} environment on {host}:{port}...")

    # run the app with the specified or default host and port
    app.run_server(host=host, port=port)


# %%



