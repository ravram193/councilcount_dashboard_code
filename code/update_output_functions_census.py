# installing packages 
import numpy as np
import pandas as pd
from copy import deepcopy
import folium
from folium.plugins import FloatImage
import base64
import plotly.graph_objects as go
import textwrap
import pickle
import re

######################################## # TAB 1 FUNCTIONS
###################

def gen_reliable_col(col_name, geo_df, metric, name_to_code_dict):
    
    """
    Creates column that duplicates estimate values for each variable, but changes unreliable values (CV <= 20) to NaN. 
    This causes their regions show up gray on the dashboard choropleth map, indicating a lack of statistical reliability.
    Called by `folium_plot()`.

    Parameters
    ----------
    col_name : str
        Variable name of the desired estimate in the geo_df
    geo_df : (Geo)DataFrame
        A dataset with demographic estimates, MOEs, and CVs aggregated by an NYC geography
    metric : str
        Sets the form the output will take (either Numbers or Percents) 
    name_to_code_dict : dict
        A dict that converts `col_name` to a variable code, which is used as a column name in geo_df

    Returns
    -------
    geo_df : (Geo)DataFrame
        Updated DF with reliability column 

    Notes
    -----
    - Columns can be accessed by adding ' (reliability)' to the end of estimate column names. 
    - These are the columns used to determine choropleth colors in `folium_plot()`

    """

    # finding estimate code (the column name for this variable in geo_df)
    var_code = name_to_code_dict[col_name] 

    if col_name == 'Unemployment rate':
        var_code_base = var_code[:-2] # this variable is always a percent ending in 'PE'
    else: 
        var_code_base = var_code[:-1] # all others end in 'E'

     # checking if column exsists in geo_df
    if (var_code in geo_df.columns):
        # to access CV column 
        CV_col_name = var_code_base + 'V' 
        # choosing which column to use based on metric
        if metric == 'Percents': 
            col_code = var_code_base + 'PE'
        elif metric == 'Numbers':
            col_code = var_code_base + 'E' # number estimate
        
        # create new column with estimate (% or #) for each variable
        geo_df = geo_df.assign(new_col=geo_df[col_code]).rename(columns={'new_col': col_code + ' (reliability)'}) 
        # convert estimates in 'reliability' columns with high CVs to NaN (high = greater than 20)
        # 'reliability' columns will be called in folium_plot to turn unreliable regions gray 
        geo_df.loc[geo_df[CV_col_name] >= 20, col_code + ' (reliability)'] = np.nan 
        
    return geo_df

###################    

def style_values_for_map(col_name, geo_df, metric, name_to_code_dict):
    
    """
    Creates columns for estimates and MOEs that are styled for the choropleth's tooltip (adds commas, percents, plus or minus). 
    Called by `folium_plot()`.

    Parameters
    ----------
    col_name : str
        Variable name of the desired estimate in the geo_df
    geo_df : (Geo)DataFrame
        A dataset with demographic estimates, MOEs, and CVs aggregated by an NYC geography
    metric : str
        Sets the form the output will take (either Numbers or Percents) 
    name_to_code_dict : dict
        A dict that converts `col_name` to a variable code, which is used as a column name in geo_df

    Returns
    -------
    geo_df : (Geo)DataFrame
        Updated DF with reliability column 

    Notes
    -----
    - Columns can be accessed by adding ' (styled)' to the end of estimate and MOE column names. 
    - These are the columns used to determine what the choropleth tooltips display in `folium_plot()`

    """

    # finding estimate code (the column name for this variable in geo_df)
    var_code = name_to_code_dict[col_name]

    # creating column for styling the numbers that will appear in tooltip
    if metric == 'Numbers': 
        # number estimate code
        col_code = var_code
        # X,XXX number format for estimate
        geo_df[col_code + ' (styled)'] = geo_df[col_code].apply(lambda x: '{:,.0f}'.format(x)) 
        # ± X,XXX number format for MOE
        geo_df[col_code[:-1] + 'M' + ' (styled)'] = '±' + geo_df[col_code[:-1] + 'M'].apply(lambda x: '{:,.0f}'.format(x)) 
    elif metric == 'Percents': 
        # % estimate code
        if col_name == 'Unemployment rate':
            col_code = var_code # this variable is always a percent ending in 'PE' 
        else: 
            col_code = var_code[:-1] + 'PE' # all others end in 'E'
        # adding %
        geo_df[col_code + ' (styled)'] = geo_df[col_code].astype(str) + '%' 
        # adding ± to % MOE       
        geo_df[col_code[:-1] + 'M' + ' (styled)'] = '±' + geo_df[col_code[:-1] + 'M'].astype(str) + '%' 
    
    # fixing this scenario
    geo_df = geo_df.replace(['±nan','±nan%', 'nan', 'nan%'], np.nan) 
    
    return geo_df 

###################

def b64_image(image_filename):

    """
    Function that encodes an image file with base64.
    Called by `folium_plot()`.

    Parameters
    ----------
    image_filename : str
        Path to image fie

    Returns
    -------
    str
        Base64-encoded string of the image, prefixed with
        'data:image/png;base64,' for embedding in HTML or web maps.
    

    """
    
    with open(image_filename, 'rb') as f:
        image = f.read()
        
    return 'data:image/png;base64,' + base64.b64encode(image).decode('utf-8')

###################

def missing_variables(geo_df, name_to_code_dict):
 
    """
    Creates entries of all "Not available" for variables missing from earlier surveys that appear in later surveys.
    This allows for continuity on the dashboard. Users will be able to click on variables regardless of the survey year 
    they've selected, and this function will handle cases where variables are missing for a given year without throwing an error. 
    
    Also updates `name_to_code_dict` with missing variables as keys and fake column names as values, which prevents key errors
    when missing variable names are called in `name_to_code_dict`. 
    
    Called by `build_table_tab1()`, `get_table_tab2()`, and `make_line_chart()`.

    Parameters
    ----------
    geo_df : (Geo)DataFrame
        A dataset with demographic estimates, MOEs, and CVs aggregated by an NYC geography
    name_to_code_dict : dict
        A dict that converts variable names to variable codes, which are used as column names in geo_df

    Returns
    -------
    geo_df : (Geo)DataFrame
        Updated dataset with "Not Available" columns added for the variables that are missing for the geo_df's survey year 
    name_to_code_dict : dict    
        `name_to_code_dict` updated with missing variable names as keys and fake column names as values 

    Notes
    -----
    - Missing variable columns can be accessed via column names with this structure: f'*missing*{code}'. All entries will be "Not available".

    """

    # dict of missing variables and their fake names created in 003_create_variable_code_dicts.ipynb
    # structure of names -> f'*missing*{code}'
    # need to use fake name instead of the actual codes because using fixed codes across all years will result in overwriting columns that use the codes for different variables in other years
    # however, will still prepare the names to be processed like normal census API codes so they seemlessly blend in with the structure of all other functions
    missing_dict = pickle.load(open(f'../data/output/missing_variables_dict.pkl', "rb")) 
    
    # the fake names of missing variables that will be added to `name_to_code_dict` 
    # these entries need to be added so that these variables don't lead to key errors when passed through `name_to_code_dict` 
    keys_to_add = [] 
    
    for var_name in missing_dict.keys():
        # creating columns with fake names to fill in missing entries for this year
        if var_name not in name_to_code_dict.keys(): 
            col_code = missing_dict[var_name]
            # all entries will be "Not available"
            geo_df[[col_code, col_code[:-1] + 'M', col_code[:-1] + 'PE', col_code[:-1] + 'PM', col_code[:-1] + 'V']] = 'Not available' 
            # list of keys to add to `name_to_code_dict`
            keys_to_add.append(var_name)

        # adding to `name_to_code_dict`
        # allows new entries to be indexed in `name_to_code_dict`
        dict_to_add = {key: missing_dict[key] for key in keys_to_add}
        name_to_code_dict.update(dict_to_add) 
    
    return geo_df, name_to_code_dict

###################

# function that generates a choropleth map displaying the distribution of a population around NYC by chosen geographic boundaries

# map specifications
zoom = 9.8
lat = 40.706000
lon = -73.976300

# to convert geographies to their full names to display in `hover_label`` on the dashboard
geo_map_dict = {'councildist_2013': 'Council District', 
                'councildist_2023': 'Council District',
                'communitydist': 'Community District',
                'schooldist': 'School District',
                'policeprct': 'Police Precinct',
                'modzcta': 'MODZCTA',
                'nta': 'NTA',
                'borough': 'Borough'}

# Data Team Logo, to be added to map
data_team_logo = '../code/assets/data-council-logo_small.png' 

# map specifications
zoom = 9.8
lat = 40.706000
lon = -73.976300

# to convert geographies to their full names to display in `hover_label`` on the dashboard
geo_map_dict = {'councildist_2013': 'Council District', 
                'councildist_2023': 'Council District',
                'communitydist': 'Community District',
                'schooldist': 'School District',
                'policeprct': 'Police Precinct',
                'modzcta': 'MODZCTA',
                'nta': 'NTA',
                'borough': 'Borough'}

# Data Team Logo, to be added to map
data_team_logo = '../code/assets/data-council-logo_small.png' 

def folium_plot(col_name, geo, geo_df, metric, name_to_code_dict, name_to_denom_dict):
    
    """
    Generates a Folium choropleth map of NYC showing a selected demographic variable at a specified geographic level.
    Generates a visual for Tab 1 of CouncilCount.

    Parameters
    ----------
    col_name : str
        Name of the desired variable.
    geo : str
        Level of geographic aggregation. Must be one of: 
        'councildist_2013', 'councildist_2023', 'policeprct', 'schooldist', 'communitydist', 'borough', 'nta', or 'modzcta'.
    geo_df : pd.DataFrame
        DataFrame containing demographic estimates, margins of error (MOEs), and coefficients of variation (CVs),
        aggregated by the selected NYC geography.
    metric : str
        Format of the variable to display. Must be either 'Numbers' or 'Percents'.
    name_to_code_dict : dict
        Dictionary mapping user-facing variable names (`col_name`) to ACS variable codes, which are used to 
        locate the correct columns in `geo_df`.
    name_to_denom_dict : dict
        Dictionary mapping a variable name (`col_name`) to the name of its denominator variable, used when calculating
        percent-based metrics for choropleth display.

    Returns
    -------
    map_name : str
        File path to the saved HTML map visualization.

    Notes
    -----
    - Regions with unreliable estimates (based on CV or MOE thresholds) are colored gray.
    - If the selected variable is unavailable in `geo_df`, a placeholder message is rendered on the map.

    """
    
    # blank map with set specifications
    fig = folium.Map(location=[lat, lon], zoom_start=zoom, tiles='cartodbpositron') 
    
    # show error message if selected variable is not available for this time
    if col_name not in name_to_code_dict.keys(): 
        # adding text explaining that data is missing for this time period
        text = "**Demographic data not available for selected time period**"
        text_html = f'<div align="center" style="position:absolute;z-index:10000;bottom:43.5%;left:50vh;max-width:250px;font-size:16pt;font-family:Gotham Medium" ><b>{text}</b></div>'
        fig.get_root().html.add_child(folium.Element(text_html))
    # if not missing, proceed with creating map
    else: 
        var_code = name_to_code_dict[col_name]
        if col_name == 'Unemployment rate': # always ends in 'PE'
            var_code_base = var_code[:-2] 
        else: # otherwise, always ends in 'E'
            var_code_base = var_code[:-1]
        # code used to access CV data in geo_df for chosen variable
        CV_col_code = var_code_base + 'V' 
        # this function prepares unreliable regions to be colored gray in the choropleth
        # values to be accessed using 'reliability' columns generated with this function
        geo_df = gen_reliable_col(col_name, geo_df, metric, name_to_code_dict) 
        # setting names in the tooltip when users hover over a region
        # value should be called Population in most cases, UR and total households are the exceptions
        if 'households' in col_name.lower():
        # if col_name == 'Total households':
            value_name = 'Households'
        elif col_name == 'Unemployment rate': 
            value_name = 'Unemployment Rate'
        else:
            value_name = 'Population'
        # setting geo_df column name and suffix for legend names based on selection of Numbers or Percents as the metric
        if metric == 'Numbers':
            # no need to add a suffix when metric is numbers
            suffix = '' 
            # codes for number estimates
            col_code = var_code
            MOE_code = col_code[:-1] + 'M'
        elif metric == 'Percents': 
            if col_name != 'Unemployment rate':
                # finding denominator so that it can be specified in the map legend for percent variables
                # using string split on ':' in case any surveys are specified in column name (don't want these displayed)               
                denom_name = name_to_denom_dict[col_name] 
                # add % to end of legend name
                suffix = ' (as % of ' + denom_name.lower().split(':')[0] + ')'    
            # if unemployment rate is selected, specify UR formula
            else:
                suffix = ' (total unemployed / total labor force)' 
                # suffix = ' (%)'
            # codes for percent estimates
            col_code = var_code_base + 'PE'
            MOE_code = var_code_base + 'PM'

            # don't want this to be lowercase
            suffix =  suffix.replace('u.s.', 'U.S.')

        # use 'reliability' columns to determine choropleth colors so only regions w/ reliable values are colored in (based on `gen_reliable_col()` output) 
        # those with NaN will be colored gray, those with values will be used in determination of region color
        # original values will still be displayed in the tooltip, just not used in the creation of the choropleth's color scheme
        columns_for_choropleth = [geo, col_code + ' (reliability)', MOE_code, CV_col_code] 
        # setting legend name
        # using string split on ':' in case any surveys are specified in column name (don't want these displayed)
        # also adding suffix estbalished above
        legend_name = col_name.split(':')[0] + suffix 
        # creates 'styled' columns with values formatted as numbers of percents for the tooltip 
        geo_df = style_values_for_map(col_name, geo_df, metric, name_to_code_dict)
    
        # outputs a choropleth map of NYC geography for the demographic variable chosen
        choropleth = folium.Choropleth(
            geo_data = geo_df,
            name = 'choropleth',
            data = geo_df,
            columns = columns_for_choropleth,
            key_on = 'feature.properties.' + geo,
            fill_color = 'Blues',
            fill_opacity = 0.7,
            line_opacity = 0.2,
            nan_fill_color='grey',
            # use_jenks = True, # check with Rose
            legend_name = '', # will add custom legend
            highlight = True,
        ).add_to(fig)

        # setting legend width
        choropleth.color_scale.width=410 
        # define custom CSS and HTML for the legend
        custom_legend_html = f"""<div style='position: fixed; top: 6vh; right: 3.25vh; width: 375px; 
                                      z-index: 9999;'>
                                 <h4 style="margin-top: 3px; padding: 0; font-size: 11px; font-weight: normal; 
                                     font-family: 'Roboto', sans-serif; word-wrap: break-word;">
                                     {legend_name}</h4></div>"""
        # add custom legend to the map
        fig.get_root().html.add_child(folium.Element(custom_legend_html))

        # display regional tooltip labels (styled values)
        # draw from styled columns for estimate and MOE values
        # still displays estimate value in tooltip even if region is grayed out based on 'reliability' values being N/A
        if geo == 'modzcta':
            # values to include in the tooltip display
            columns_for_tooltip = [geo, 'ZCTA', col_code + ' (styled)', MOE_code + ' (styled)', CV_col_code] 
            # aliases
            aliases = ['MODZCTA', 'ZCTA(s) Represented', value_name, 'Margin of Error', 'Coefficient of Variation'] 
        elif geo == 'nta':
            columns_for_tooltip = [geo, 'nta_code', col_code + ' (styled)', MOE_code + ' (styled)', CV_col_code] 
            aliases = ['NTA Name', 'NTA Code', value_name, 'Margin of Error', 'Coefficient of Variation'] 
        else:
            columns_for_tooltip = [geo, col_code + ' (styled)', MOE_code + ' (styled)', CV_col_code] 
            aliases = [geo_map_dict[geo], value_name, 'Margin of Error', 'Coefficient of Variation'] 
        # adding tooltip values and aliases
        choropleth.geojson.add_child( 
            folium.features.GeoJsonTooltip(columns_for_tooltip, aliases=aliases, labels=True)) 
                
    # adding Data Team logo
    FloatImage(b64_image(data_team_logo), bottom=1, left=1).add_to(fig)
      
    # generate map as html for embedding in the dashboard
    map_name = '../visuals/dashboard_map.html'
    
    fig.save(map_name)
    
    return map_name

###################

# creates table comparing values between NYC-wide value for a variable and the value for selected geographies (such as council districts)

geo_table_dict = {'councildist_2013': 'Council District', # to convert geographies to their displayed names in the table 
                  'councildist_2023': 'Council District',
                  'communitydist': 'Community District',
                  'schooldist': 'School District',
                  'policeprct': 'Police Precinct',
                  'modzcta': 'MODZCTA',
                  'nta': '',
                  'borough': '',
                  'city': ''}

def build_table_tab1(geo, geo_nums, geo_df, selected_demo, metric, name_to_code_dict, conversion_dict):  

    """
    Builds a formatted table of demographic estimates, margins of error (MOE), and 
    coefficients of variation (CV) for selected NYC geographic regions. Called by `get_table_tab1()`.

    Parameters
    ----------
    geo : str
        The geographic aggregation level. Must be one of the following: 'council_2013', 'council_2023', 'policeprct', 'communitydist', 'schooldist', 'communitydist', 'borough', 'modzcta', or 'nta'.
    geo_nums : list
        List of specific geographic identifiers selected by the user (e.g., district numbers or borough names).
    geo_df : gpd.GeoDataFrame
        A GeoDataFrame containing demographic estimates, margins of error (MOE), and coefficient of variation (CV) 
        aggregated by the specified NYC geography.
    selected_demo : str
        The value of the selected demographic variable shown in the dashboard dropdown menu.
    metric : str
        The metric to display in the table. Must be either 'Numbers' or 'Percents'.
    name_to_code_dict : dict
        A dictionary mapping human-readable variable names to ACS variable codes 
    conversion_dict : dict 
        Dictionary mapping region names to user-facing names (enter nta_dict for nta) 

    Returns
    -------
    table : pd.DataFrame
        A DataFrame with one row per selected region, containing:
        - 'Region': human-readable region name
        - 'Estimate': formatted estimate value (with optional asterisk for unreliability)
        - 'MOE': margin of error, similarly formatted
        - 'CV': coefficient of variation

    Notes
    -----
    - Estimates with CV >= 20 are flagged with an asterisk (*) to indicate potential unreliability.
    - Missing or unavailable values are replaced with '-'.
    - Formatting differs for numeric vs. percent metrics (adds '%' or thousands separator).
    - If a variable is missing from `geo_df`, a placeholder column is created via `missing_variables()`.
    """

    # blank table
    table = pd.DataFrame()
    
    # filling in missing values with 'Not available', updating `name_to_code_dict` with fake codes
    geo_df, name_to_code_dict = missing_variables(geo_df, name_to_code_dict)  

    # access the API code associated with this variable, which is used for its column name for in the geo_df
    var_code = name_to_code_dict[selected_demo]
          
    # setting `var_code_base` to help access various codes
    if selected_demo == 'Unemployment rate':
        var_code_base = var_code[:-2] # always ends in 'PE'
    else:
        var_code_base = var_code[:-1] # otherwise, ends in 'E'   
    # code used to access CV data in geo_df for chosen variable
    CV_col_code = var_code_base + 'V' 
    
    # cycling through list of selected geo regions to collect estimates for them
    for num in geo_nums: 
        # for labeling the column in user-facing table
        if geo == 'nta': 
            # so abbreviated name appears in the table (some NTA names get really long otherwise)
            column_name = conversion_dict[num] 
        else:
            # example: 'Council District 1'
            column_name = geo_table_dict[geo] + ' ' + str(num)  

        # setting geo_df column names and value suffixes based on selection of Numbers or Percents
        if metric == 'Percents':
            col_code = var_code_base + 'PE'
            MOE_code = var_code_base + 'PM'
        else:
            col_code = var_code_base + 'E'
            MOE_code = var_code_base + 'M'

        # setting up NYC-wide estimates

        # will add asterisk to estimate if CV is 20 or greater to indicate lack of reliability    
        if (geo_df[CV_col_code][num] not in ['Not available', np.nan]) and (geo_df[CV_col_code][num] >= 20): 
            reliable_nyc = '*'
        else:
            reliable_nyc = ''

        # finding demographic estimate/ MOE/ CV for NYC overwriting as blank if value is null (otherwise 'nan' appears as text)
        geo_val = '-' if (geo_df[col_code][num] == 'Not available') or (np.isnan(geo_df[col_code][num])) else geo_df[col_code][num]
        geo_MOE_val = '-' if (geo_df[MOE_code][num] == 'Not available') or (np.isnan(geo_df[MOE_code][num])) else geo_df[MOE_code][num]
        geo_CV_val = '-' if (geo_df[CV_col_code][num] == 'Not available') or (np.isnan(geo_df[CV_col_code][num])) else geo_df[CV_col_code][num]

        # formatting values
        if metric == 'Numbers':
            if (geo_val != '-'):
                geo_val = reliable_nyc + str('{:,.0f}'.format(float(geo_val))) # looks like -> #,###
            if (geo_MOE_val != '-'):
                geo_MOE_val = reliable_nyc + str('{:,.0f}'.format(float(geo_MOE_val)))
        else:
            if (geo_val != '-'):
                geo_val = reliable_nyc + str(geo_val) + '%' # looks like -> ##.##%
            if (geo_MOE_val != '-'):
                geo_MOE_val = reliable_nyc + str(geo_MOE_val) + '%'

        # adding row for selected region(s)
        new_row = {'Region':column_name,'Estimate':geo_val, 'MOE':geo_MOE_val, 'CV':geo_CV_val}
        new_row_df = pd.DataFrame([new_row])
        table = pd.concat([table, new_row_df], ignore_index=True)
#         table = table.append(pd.Series(new_row, index=new_row.keys(), name=column_name)) 
        
    return table

###################

def get_table_tab1(geo, geo_nums, geo_df, nyc_wide_df, selected_demo, metric, name_to_code_dict, conversion_dict, rank = None):  

    """
    Generates a comparison table of demographic estimates for selected NYC geographies and includes a row for NYC-wide statistics.
    Runs `build_table_tab1()` to do so. Creates a visual for Tab 1 of CouncilCount.

    Parameters
    ----------
    geo : str
        The geographic aggregation level. Must be one of the following: 'council_2013', 'council_2023', 'policeprct', 'communitydist', 'schooldist', 'communitydist', 'borough', 'modzcta', or 'nta'.
    geo_nums : list
        List of specific geographic identifiers selected by the user (e.g., district numbers or borough names).
    geo_df : gpd.GeoDataFrame
        A GeoDataFrame containing demographic estimates, margins of error (MOE), and coefficient of variation (CV) 
        aggregated by the specified NYC geography.
    nyc_wide_df : pd.DataFrame
        A DataFrame containing citywide demographic estimates, MOE, and CV.
    selected_demo : str
        The value of the selected demographic variable shown in the dashboard dropdown menu.
    metric : str
        The metric to display in the table. Must be either 'Numbers' or 'Percents'.
    name_to_code_dict : dict
        A dictionary mapping human-readable variable names to ACS variable codes 
    conversion_dict : dict 
        Dictionary mapping region names to user-facing names (enter nta_dict for nta) 
        - Default is None
    rank : bool, optional 
        If True, sort the table from high to low based on estimate values.
        If False, sort from low to high.
        If None (default), do not apply any sorting.

    Returns
    -------
    mycolumns : list of dict
        List of dictionaries specifying table column headers, each with 'name' and 'id' keys.
    table_label : str
        A label to be displayed above the table, summarizing the comparison (e.g., "Borough Comparison: Total population").
    nyc_table : pd.DataFrame
        A DataFrame containing the demographic estimates for NYC and selected geographies, 
        formatted and optionally ranked.
        
    """

    # creating NYC row automatically for every table
    NYC_row = build_table_tab1('city', ['New York City'], nyc_wide_df, selected_demo, metric, deepcopy(name_to_code_dict), conversion_dict = None)
    # adding selected regions
    geo_rows = build_table_tab1(geo, geo_nums, geo_df, selected_demo, metric, deepcopy(name_to_code_dict), conversion_dict)

    nyc_table = pd.concat([NYC_row, geo_rows], ignore_index=True)
    mycolumns = [{'name': i, 'id': i} for i in nyc_table.columns] # columns for table
    table_label = geo_map_dict[geo] + ' Comparison: ' + selected_demo.split(':')[0] # text above the table

    # sorting table (high-low or low-high)
    if rank != None:
        # gathering all estimates and their indices
        string_dict = dict(zip(nyc_table.index.to_list(), nyc_table['Estimate'].to_list())) 
        # if blank, convert to zero
        string_dict = {k: '0' if v == '-' else v for k, v in string_dict.items()} 
        # removing non-numeric characters
        string_dict_cleaned = {k: float(re.sub(r'[^\d.]', '', v)) for k, v in string_dict.items()} 
        # ranking order low to high (True for high to low, False for low to high)
        sorted_strings_dict = dict(sorted(string_dict_cleaned.items(), key=lambda item: item[1], reverse=rank)) 

        # list of indices in order from high to low values
        sorted_index_list = sorted_strings_dict.keys() 
        # changing order of dataframe based on the index order
        nyc_table = nyc_table.reindex(sorted_index_list) 
    
    return mycolumns, table_label, nyc_table # column names, label, and table itself

######################################## # TAB 2 FUNCTIONS

###################

def gen_var_group(groups, variable_dict):
    
    """
    This function accesses all variable codes associated with an overarching category.
    Called by `get_table_tab2()`.

    Parameters
    ----------
    group : list
        Group of variable category names (e.g. Race, Education, Age, etc.)
    variable_dict : list
        A list of dictionaries with variable values, labels, and their groups
        - Used to create the dropdown menus of available variables in the dashboard code (006_councilcount_dashboard.ipynb)

    Returns
    -------
    var_dict : dict
        A dict that associates selected variable categories with their component deomgraphic variables

    """
    
    var_dict = {}
    
    # converting variable_dict to df
    var_group_df = pd.DataFrame(variable_dict).drop(columns=['label']) 
    
    # iterating through list of topic names
    for group in groups: 
        
        # creating list of variables associated with given group name
        var_list = var_group_df.loc[var_group_df['group'] == group, 'value'].unique().tolist()
        
        # adding list of variables to dict, with group name as key
        var_dict[group] = var_list 
    
    return var_dict

###################

def gen_dif_col(table_df, metric):

    """
    Adds a column indicating if the difference between two compared values in a DF row is statistically significant.
    Called by `get_table_tab2()`.

    Parameters
    ----------
    table_df : pd.DataFrame
        Table created by `get_table_tab2()` with estimates, MOEs, and CVs for selected variables and regions
    metric : str
        Sets form output will take (either 'Numbers' or 'Percents')

    Returns
    -------
    table_df : pd.DataFrame
        The original DF updated with a difference column

    Notes
    -----
    - An asterisk will be added to a difference column value if one estimate's CV >= 20 
      or the confidence intervals for two estimates overlap

    """

    # copying table_df so that edits made do not affect the original
    df = deepcopy(table_df) 
        
    # finding all of the column names that will be used
    geo_region1 = df.columns[1][0]
    geo_region2 = df.columns[4][0] 

    est_col1 = (geo_region1, 'Estimate')
    est_col2 = (geo_region2, 'Estimate')
    moe_col1 = (geo_region1, 'MOE')
    moe_col2 = (geo_region2, 'MOE')
    cv_col1 = (geo_region1, 'CV')
    cv_col2 = (geo_region2, 'CV')
    dif_col = ('','Difference')
    demo_col = ('', '')
        
    table_df[dif_col] = ''

    for ind in df.index: 

        # converting values to floats
        df[est_col1] = [re.sub('[%,*]','',s)  if s != '-' else '-' for s in df[est_col1]]
        df[est_col2] = [re.sub('[%,*]','',s) if s != '-' else '-' for s in df[est_col2]]

        # if Estimate is unavailable, set Difference to '-'
        if ('-' in [df.loc[ind, est_col1], df.loc[ind, est_col2]]):
            table_df.loc[ind, dif_col] = '-'
        else:
            # will use to calculate the difference between each estimate
            estimate1 = float(df.loc[ind, est_col1])
            estimate2 = float(df.loc[ind, est_col2])
            # format based on metric
            # pop variables will always be numbers
            if (df.loc[ind, demo_col] in ['Total population', 'Total households']):  
                dif = '{:,.0f}'.format(round(estimate1 - estimate2,2))
            # UR will always be percent
            elif (metric == 'Percents') or (df.loc[ind, demo_col] == 'Unemployment rate'): 
                dif = str(round(estimate1 - estimate2,2)) + '%'
            elif (metric == 'Numbers'):
                dif = '{:,.0f}'.format(round(estimate1 - estimate2,2))
            # fill Difference column
            table_df.loc[ind, dif_col] = dif 

        # need to set Difference to '-' when the MOE is '-' (comes up in cases where Estimate is 0)
        if ('-' in [df.loc[ind, moe_col1], df.loc[ind, moe_col2]]):
            table_df.loc[ind, dif_col] = '-'
        # add symbol if there is overlap btwn MOEs and/ or one of the estimates is unreliable
        else: 
            df[moe_col1] = [re.sub('[%,*]','',s) if s != '-' else '-' for s in df[moe_col1]]
            df[moe_col2] = [re.sub('[%,*]','',s) if s != '-' else '-' for s in df[moe_col2]]
            moe1 = float(df.loc[ind, moe_col1])
            moe2 = float(df.loc[ind, moe_col2])
            # add symbol if they overlap
            if (abs(estimate1 - estimate2) < moe1 + moe2) or (df.loc[ind, cv_col1] >= 20) or (df.loc[ind, cv_col2] >= 20): 
                table_df.loc[ind, dif_col] = '*' + dif
                    
    return table_df

###################

def get_table_tab2(geo1, geo_num1, geo_df1, geo2, geo_num2, geo_df2, groups, metric, name_to_code_dict, variable_dict, conversion_dict, rel_info=False):
    
    """
    Generates a formatted comparison table of demographic estimates, MOEs, and CVs 
    for two selected NYC geographic regions. Used to generate the visual for Tab 2 on CouncilCount.

    Parameters
    ----------
    geo1 : str
        Aggregation level for the first selected region. Must be one of the following: 
        'councildist_2013', 'councildist_2023', 'policeprct', 'schooldist', 'communitydist', 'borough', 'nta', 'modzcta', or 'city'.
    geo_num1 : str or int
        Specific geographic unit selected (e.g., council district number or borough name) for `geo1`.
    geo_df1 : pd.DataFrame
        DataFrame with demographic estimates, MOEs, and CVs aggregated by the `geo1` geography.
    geo2 : str
         Aggregation level for the second selected region. Must be one of the following: 
        'councildist_2013', 'councildist_2023', 'policeprct', 'schooldist', 'communitydist', 'borough', 'nta', 'modzcta', or 'city'.
    geo_num2 : str or int
        Specific geographic unit selected (e.g., council district number or borough name) for `geo2`.
    geo_df2 : pd.DataFrame
        DataFrame with demographic estimates, MOEs, and CVs aggregated by the `geo2` geography.
    groups : list of str
        List of demographic groups to include (e.g., ['Race', 'Education', 'Age']).
    metric : str
        Sets form output will take (either 'Numbers' or 'Percents').
    name_to_code_dict : dict
        Dictionary mapping user-facing column names to ACS variable codes used in the geo_dfs.
    variable_dict : list of dict
        List of dictionaries with keys 'value', 'label', and 'group' used to organize variables by group.
    conversion_dict : dict
        Dictionary mapping internal region names to user-facing names (e.g., nta_dict for NTA names).
    rel_info : bool
        Whether to include reliability information (e.g., MOE and CV columns) in the final output.

    Returns
    -------
    comparison_df : pd.DataFrame
        A formatted table comparing selected demographic variables between two NYC geographies.

    Notes
    -----
    - Unemployment rate will always be displayed as a percent regardless of metric chosen
    - Total population and total households will always be displayed as numbers regardless of metric chosen

    """
    
    # setting both of the chosen regions' names
    for num, geo, geo_num in [(1, geo1, geo_num1), (2, geo2, geo_num2)]: 
        if geo == 'nta': 
            # abbreviating names
            globals()[f'sel_region{num}'] = conversion_dict[geo_num]
        elif 'council' in geo: 
            # stating boundary year
            globals()[f'sel_region{num}'] = geo_table_dict[geo] + ' ' + str(geo_num) + ' (' + geo[-4:] + ')'
        elif geo == 'city': 
            # so gets labeled correctly even though their is no 'region'
            globals()[f'sel_region{num}'] = 'New York City'
        else:
            # else, print region name and region number
            globals()[f'sel_region{num}'] = geo_table_dict[geo] + ' ' + str(geo_num)
        
    # getting list of variables chosen by user, will be used to access values from geo_df and to name rows in final_table
    
    # creating dict that associates list of demographics with each topic group
    groups_dict = gen_var_group(groups, variable_dict) 
    var_name_list = []
    # for each topic group (e.g. Race, Education, etc)
    for group in groups: 
        # adding list of variable names associated with each topic group
        var_name_list = var_name_list + groups_dict[group]
    
    for geo_df in [geo_df1, geo_df2]:
        # filling in missing values with 'Not available', updating name_to_code_dict with fake codes
        geo_df, name_to_code_dict_updated = missing_variables(geo_df, deepcopy(name_to_code_dict))
                
    # creating final table 

    # table where all results will go
    final_table = pd.DataFrame() 
    # preparing columns
    final_table = pd.DataFrame({(sel_region1, 'Estimate'):{},(sel_region1, 'MOE'):{},(sel_region1, 'CV'):{},
                                (sel_region2, 'Estimate'):{},(sel_region2,'MOE'):{},(sel_region2,'CV'):{}})

    # looping through each set of DFs 
    for num, geo, geo_num, geo_df in [(1, geo1, geo_num1, geo_df1), (2, geo2, geo_num2, geo_df2)]:        
        # so that nyc_wide_df is properly indexed later in the code
        if geo == 'city': geo_num = 'New York City'       
        # collecting variable codes from names using conversion dict
        var_code_list = [name_to_code_dict_updated[var] for var in var_name_list] 
        # keeping track of total population codes, if they've been requested
        total_pop_codes = [name_to_code_dict_updated[var] for var in var_name_list if ('Total population' in var) or ('Total household' in var)]
        # updating list of variable column names based on metric chosen
        if metric == 'Numbers': suffix = 'E'
        elif metric == 'Percents': suffix = 'PE'
        # getting list of estimate column names based on var_code_list and metric 
        # exceptions for unemployment rate which will always be %, and total pop codes which always should always be #s
        estimates_list = [var[:-1] + suffix if ((not var.endswith('PE')) and (var not in total_pop_codes)) else var for var in var_code_list]
        # getting list of MOE column names based on estimate_list
        moe_list = [var[:-1] + 'M' for var in estimates_list] 
        # getting list of CV column names 
        # with exception for unemployment rate which always ends in PE
        cv_list = [var[:-1] + 'V' if not var.endswith('PE') else var[:-2] + 'V' for var in var_code_list]
        # subsetting to the estimates included in the group, in selected region
        globals()[f'estimates{num}'] = geo_df.loc[geo_num, estimates_list].to_dict() 
        # subsetting to the MOEs included in the group, in selected region
        globals()[f'MOE{num}'] = geo_df.loc[geo_num, moe_list].to_dict() 
        # subsetting to the CVs included in the group, in selected region
        globals()[f'CV{num}'] = geo_df.loc[geo_num, cv_list].to_dict() 

    # using string split on ':' in case any surveys are specified in column name (don't want these displayed)               
    var_name_list_for_naming = [var.split(':')[0] for var in var_name_list]
    # adding values to table
    for estimates, MOE, CV, sel_region in [(estimates1, MOE1, CV1, sel_region1), (estimates2, MOE2, CV2, sel_region2)]:
        final_table[(sel_region, 'Estimate')] = estimates.values()
        final_table[(sel_region, 'MOE')] = MOE.values()
        final_table[(sel_region,'CV')] = CV.values()
    # adding demographic variable names for each group
    final_table.insert(loc=0, column='index', value=var_name_list_for_naming) 
    final_table = final_table.set_index('index')    
            
    # formatting table values
    for sel_region in [sel_region1, sel_region2]:
        # adding mark reliability marker when CV >= 20
        for ind in final_table.index:
            for col in final_table[sel_region].columns:
                if (final_table.loc[ind, (sel_region, 'CV')] != 'Not available') and (final_table.loc[ind, (sel_region, 'CV')] >= 20) : rel_marker = '*'
                else: rel_marker = ''
                # formatting estimate and MOE columns (excluding cases where value is unavailable)
                if (('Estimate' in col) or ('MOE' in col)) and (final_table[sel_region].loc[ind, col] != 'Not available'):
                    if  (ind in ['Total population', 'Total households']) or \
                            ((metric == 'Numbers') and 
                            (ind != 'Unemployment rate') and 
                            (final_table[sel_region].loc[ind, col] != 'Not available')):
                        #add comma(s), remove decimals for number values
                        final_table.loc[ind, (sel_region, col)] = rel_marker + '{:,.0f}'.format(final_table.loc[ind, (sel_region, col)])  
                    else:
                        # add % for percent values
                        final_table.loc[ind, (sel_region, col)] = rel_marker + str(final_table.loc[ind, (sel_region, col)]) + '%' 

    # overwriting NaN as blank 
    final_table = final_table.replace([np.nan, 'nan', 'nan%', 'Not available', 'Not available%'], '-') 
    
    # reseting index so that this column will be read in by DashTable
    final_table = final_table.reset_index() 
    final_table = final_table.rename(columns={'index': ''}, level=0)
    #final_table = final_table.rename(columns={'':''}, level=1) # if want to add name to variable column use this code
    
    # adding difference column
    final_table = gen_dif_col(final_table, metric) 
        
    # remove reliability column if not asked for it
    if rel_info == False: 
        final_table = final_table.drop(columns=[(sel_region1, 'MOE'), (sel_region1, 'CV'), (sel_region2, 'MOE'), (sel_region2, 'CV')])
        
    # label for table in Dash app
    tabel_label = 'Comparing ' + sel_region1 + ' to ' + sel_region2 
    
    return tabel_label, final_table

###################

def convert_df_to_dash(df):

    """
    Converts a pandas DataFrame to a format accepted by Dash. Used to create the table on Tab 2 in CouncilCount.

    Parameters
    ----------
    df : pd.DataFrame
        Table produced by `get_table_tab2()`

    Returns
    -------
    cols, data : lists
        Columns and data in the format Dash requires 

    """

    # create ids for multi indexes (single index stays unchanged)
    # [('', 'A'), ('B', 'C'), ('D', 'E')] -> ['A', 'B_C', 'D_E']
    ids = ["".join([col for col in multi_col if col]) for multi_col in list(df.columns)]

    # build columns list from ids and columns of the dataframe
    cols = [{"name": list(col), "id": id_} for col, id_ in zip(list(df.columns), ids)]

    # build data list from ids and rows of the dataframe
    data = [{k: v for k, v in zip(ids, row)} for row in df.values]

    return cols, data

###################

def set_color(df, var_code, moe_code, cv_code):

    """
    Creates list of colors and coordinates, which are used to change markers/ error bars of statistically insigificant values to grey.
    Also sets opacity levels for the lines connecting each point (line connecting missing point(s) will have 0 opacity).
    Called by `make_line_chart()`.

    Parameters
    ----------
    df : pd.DataFrame
        Table created in `make_line_chart()`
    var_code : str
        Chosen census variable's API code
    moe_code: str
        Chosen census variable's margin of error's API code
    cv_code: str
        Chosen census variable's CV's code

    Returns
    -------
    fig : plotly.graph_objs.Figure
        An interactive Plotly line chart showing ACS estimates, margins of error, and reliability indicators over time.
    
    """
    
    color_list = []
    year_list = []
    demo_list = []
    opacity_list = []
    
    # setting color based on if statistically significant
    for ind in df.index: 
        year_list.append(df.loc[ind, 'Year'])
        if df.loc[ind, moe_code] != 'Not available':
            demo_list.append(df.loc[ind, var_code])
            if  df.loc[ind, cv_code] >= 20:
                color_list.append('#A9A9A9') # grey
            else:
                color_list.append('#0000FF') # blue  
        elif df.loc[ind, moe_code] == 'Not available':
            color_list.append('rgba(0,0,0,0)') # transparent
            demo_list.append(-1)

    # setting line segment opacity between each point 
    indices = [i for i, item in enumerate(df[var_code].to_list()) if item == -1]
    # creates a list of 0s for each index (0 opacity) 
    opacity_list = [0] * len(indices)  
    loops_left = 2 - len(opacity_list)

    # add 1s for remaining loops (full opacity)
    if loops_left > 0:
        opacity_list.extend([1] * loops_left)  
        
    return color_list, year_list, demo_list, opacity_list

###################

# creates line chart with error bars comparing one variable's values over time

# to convert geographies to their displayed names in the table 
geo_chart_dict = {'councildist_2013': 'Council District', 
                  'councildist_2023': 'Council District',
                  'communitydist': 'Community District',
                  'schooldist': 'School District',
                  'policeprct': 'Police Precinct',
                  'modzcta': 'MODZCTA',
                  'nta': '',
                  'borough': '',
                  'city': 'NYC'
                }

def make_line_chart(selected_demo, geo, geo_num, geo_dfs, years, metric, name_to_code_dicts, name_to_denom_dict, conversion_dict = None):
    
    """
    Generates an interactive Plotly line chart of ACS 5-Year estimates for a selected demographic variable 
    across multiple time periods and a specified NYC geography.

    Parameters
    ----------
    selected_demo : str
        The selected demographic variable
    geo : str
        Geographic level of aggregation (e.g., 'councildist_2013', 'councildist_2023', 'policeprct', 'schooldist', 'communitydist', 'borough', 'modzcta', 'nta', 'city').
    geo_num : str or int
        The geographic identifier (e.g., borough name, council district number, or 0 if geo='nyc').
    geo_dfs : list of (g)pd.(Geo)DataFrames
        List of (geo)dataframes containing estimates, MOEs, and CVs for the selected geography across multiple years.
    years : list of int
        List of ACS 5-Year end years (e.g., [2011, 2016, 2021]).
    metric : str
        Display format of the data. Must be one of: 'Numbers' or 'Percents'.
    name_to_code_dicts : list of dict
        List of dictionaries mapping human-readable variable names to ACS variable codes, one per year.
    name_to_denom_dict : dict
        Dictionary mapping human-readable variable names to the ACS variable name of the denominator (for percent-based variables).
    conversion_dict : dict, optional
        Dictionary mapping geographic identifiers to human-readable labels (e.g., NTA codes to NTA names). Only needed if geo='nta'.

    Returns
    -------
    fig : plotly.graph_objs.Figure
        An interactive Plotly line chart showing ACS estimates, margins of error, and reliability indicators over time.

    Notes
    -----
    - The chart includes error bars based on margins of error.
    - Grey markers for a year indicate that an estimate is not statistically reliable based on the coefficient of variation.
    - If data is not available for a particular time period, it will remain blank on the chart.
    
    """
            
    # collecting values for table
    year_range_list = [] 
    demo_values = []
    moe_values = []
    cv_values = []
    
    if geo == 'city': 
        geo_num = 'New York City' 

    # number of loops set by length of year list
    for num in list(range(1,len(years)+1)): 
        # creating name_to_code_dict for this year
        globals()[f'name_to_code_dict{num}'] = name_to_code_dicts[num-1]
        # creating local variables
        globals()[f'geo_df{num}'] = geo_dfs[num-1]
        # # filling in values of 'Not available' for missing demo columns
        # globals()[f'geo_df{num}'], globals()[f'name_to_code_dict{num}'] = missing_variables(globals()[f'geo_df{num}'], globals()[f'name_to_code_dict{num}'])
        # creating year ranges for column naming purposes
        globals()[f'year_range{num}'] = str(years[num-1]-4) + '-' + str(years[num-1]) 
        year_range_list.append(globals()[f'year_range{num}'])
        # filling in missing values with 'Not available', updating name_to_code_dict with fake codes
        globals()[f'geo_df{num}'], globals()[f'name_to_code_dict{num}'] = missing_variables(globals()[f'geo_df{num}'], globals()[f'name_to_code_dict{num}']) 
        # list of values for table
        if selected_demo == 'Unemployment rate': # always ends with 'PE'
            var_code_base = globals()[f'name_to_code_dict{num}'][selected_demo][:-2]
        else: 
            var_code_base = globals()[f'name_to_code_dict{num}'][selected_demo][:-1]
        # building code names, which will be used to pull data from geo_df columns
        if (metric == 'Numbers'): suffix = 'E' 
        elif (metric == 'Percents'): suffix = 'PE'
        var_code = var_code_base + suffix
        MOE_code = var_code[:-1] + 'M'
        cv_code = var_code_base + 'V'
        # excluding missing values
        if globals()[f'geo_df{num}'].loc[geo_num, var_code] == 'Not available': 
            demo_values.append(-1)
        else:
            demo_values.append(globals()[f'geo_df{num}'].loc[geo_num, var_code])

        moe_values.append(globals()[f'geo_df{num}'].loc[geo_num, MOE_code])

        # if Percent, selected_demo needs '%' removed for CV columns name
        if globals()[f'geo_df{num}'].loc[geo_num, MOE_code] == 'Not available': # excluding missing values
            cv_values.append(100)
        else:
            cv_values.append(globals()[f'geo_df{num}'].loc[geo_num, cv_code])
                
    # building table of values across each year
    table = pd.DataFrame({'Year':year_range_list, var_code:demo_values, 
                          MOE_code: moe_values, cv_code: cv_values})
    
    # setting marker, error bar colors based on CV (grey for greater than or equal two 20, blue otherwise)
    colors, years, values, opacities = set_color(table, var_code, MOE_code, cv_code) 
  
    # creating the scatter plot with error bars
    fig = go.Figure(data=go.Scatter( 
        x=years,
        y=values,
        opacity=0,
        error_y=dict(
            type='data', # value of error bar given in data coordinates
            array=table[MOE_code],
            visible=True),
    ))
    
    # customizing hover labels and title/ axis label text
    fig.update_layout(
        font=dict(family="Gotham Light", color='black', size=12), # axis numbers/ labels font
        title_font_family='Gotham Medium',
        title_font_color='black',
        showlegend=False, 
        hoverlabel=dict(
            bgcolor='white',
            font_size=14,
            font_family='Gotham Light'
        )
    )
        
    # setting error bar color
    for i, bar in enumerate(table[MOE_code]):  
        fig.add_trace(go.Scatter(
                        x=[years[i]],
                        y=[values[i]],
                        error_y=dict(type='data', color = colors[i],array=[bar],visible=True), # setting error bar color based on reliability (CV)
                        hoverlabel = dict(namelength=0), # hide when hovering on error bars
                    ))
    
    # setting marker style
    fig.add_trace(go.Scatter(x=years, y=values, mode = 'markers',
                     marker_symbol = 'circle', # shapes
                     marker_color = colors, # marker color based on reliability (CV)
                     marker_size = 10,
                     marker=dict(opacity=1,line=dict(width=0)), # no marker outlines
                     hoverinfo='skip' # hide when hovering on marker
                ))
        
    # setting opacity of each line segment (will be invisible when connecting a missing point to an existing point)    
    for i in range(len(years) - 1):
        fig.add_trace(go.Scatter(
            x=[years[i], years[i + 1]], 
            y=[values[i], values[i + 1]], 
            mode='lines',
            line=dict(color='blue', width=3),
            opacity=opacities[i]  # set opacity for each segment
        ))
    
    # for labeling purposes below
    if geo == 'city': geo_num = '- wide' 
    
    # setting label based on chosen variable
    if 'household' in selected_demo.lower(): pop = 'Households' 
    else: pop = 'Population'
    
    if selected_demo == 'Unemployment rate': 
        yaxis_label = 'Rate (%)' 
        suffix = ' (total unemployed / total labor force)'
    elif (metric == 'Percents'): 
        yaxis_label = '% of ' + pop 
        # collecting denominator information for percent variables
        denom_name = name_to_denom_dict[selected_demo].split(':')[0].lower()
        # don't want this to be lowercase
        denom_name = denom_name.replace('u.s.', 'U.S.')
        suffix = ' (as % of ' + denom_name.split(':')[0] + ')' 
    else: 
        yaxis_label = pop
        suffix = ''
        
    # changing to shorter names
    if geo == 'nta': geo_num = conversion_dict[geo_num] 
    
    # creating title (wraps after certain # of characters)    
    title_text = geo_chart_dict[geo] + ' ' + str(geo_num) + ': ' + selected_demo.split(':')[0] + suffix
    split_text = textwrap.wrap(title_text, width=60)
    title = '<br>'.join(split_text)

    fig.update_layout(
     title={
        'text': title,
        'x': 0.5, # center title
        'y': 0.9,
        'xanchor': 'center',
        'yanchor': 'top',
        'font': {'size': 14}
     },
     xaxis_title="American Community Survey 5-Year Time Period",
     yaxis_title=yaxis_label,
     margin=dict(t=100), # adjust top margin to accommodate title
     autosize=True
    )
    
    fig.update_yaxes(title_font_family='Gotham Medium', title_font_color="black")
    fig.update_xaxes(title_font_family='Gotham Medium', title_font_color="black")
    
    return fig

###################

# misc function (doesn't belong to any individual tab)

def create_name_to_code_dict(data_dictionary_df, denoms = False):

    """
    Creates a dictionary pairing variable names to variable codes for the 5-Year ACS.
    There is also an option to pair variable names to denominator variables as well.

    Parameters
    ----------
    data_dictionary_df : pd.DataFrame
        A data dictionary for the requested ACS survey variables
    denoms : boolean
        Option to pair variable names to denominator variables instead of codes
        - Default is False
             
    Returns
    -------
    dict
        - If denoms is False:
            Keys = variable names 
            Values = variable codes 
        - If denoms is True:
            Keys = variable names 
            Values = denominator variable names

    """

    data_dictionary = data_dictionary_df.copy()

    # if there are duplicate variables names from different surveys, add survey name to variable name to help distinguish
    dup_names = data_dictionary.loc[data_dictionary.duplicated('estimate_description')]['estimate_description'].to_list()
    data_dictionary.loc[data_dictionary['estimate_description'].isin(dup_names), 'estimate_description'] = data_dictionary.loc[data_dictionary['estimate_description'].isin(dup_names), 'estimate_description'].str.strip() +  ': ' + data_dictionary.loc[data_dictionary['estimate_description'].isin(dup_names), 'acs_survey'].str.strip()

    # option to pair names to denominators instead of codes
    if denoms == True:
        # if there are duplicate denominator names from different surveys, add survey name to denominator name to help distinguish
        data_dictionary.loc[data_dictionary['denominator_description'].isin(dup_names), 'denominator_description'] = data_dictionary.loc[data_dictionary['denominator_description'].isin(dup_names), 'denominator_description'].str.strip() +  ': ' + data_dictionary.loc[data_dictionary['denominator_description'].isin(dup_names), 'acs_survey'].str.strip()
        name_to_denom_dict = dict(zip(data_dictionary['estimate_description'], data_dictionary['denominator_description']))
        return name_to_denom_dict
    # otherwise, stick with matching name to codes
    else:
        # create name_to_code_dict (use to identify the code for each variable)
        name_to_code_dict = dict(zip(data_dictionary['estimate_description'], data_dictionary['estimate_var_code']))
        return name_to_code_dict
