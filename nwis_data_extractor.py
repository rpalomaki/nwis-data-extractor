# -*- coding: utf-8 -*-

import json
from urllib.request import urlopen
from datetime import datetime
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

def build_url(**kwargs):
    """
    This function generates a url to request data from from the USGS Water
    Data website. Instantaneous values are used by default. To retrieve daily 
    values instead, pass kwarg data='dv'. Output format is JSON.
    
    Returns: url as string
    
    Parameters
    ----------    
    Other kwargs used in this fuction should be valid USGS URL arguments. A 
    complete list and documentation of these arguments can be found at 
    https://waterservices.usgs.gov/rest/IV-Service.html#URLFormat.    
    """
    #Start with base url
    if 'dv' in kwargs.items():
        url = 'http://waterservices.usgs.gov/nwis/dv/?format=json&siteStatus=all'
    else:
        url = 'http://waterservices.usgs.gov/nwis/iv/?format=json&siteStatus=all'
    
    #Gather all kwargs and append to base url
    for key, value in kwargs.items():
        if len(value) == 1:
            #Append url arguments with a single value
            url = url + '&' + str(key) + '=' + str(value)
        
        else:
            #Arguments with multiple values handled differently
            values = ''
            for val in value:
                values = values + str(val) + ','
            #Slice values string to remove trailing comma
            url = url + '&' + str(key) + '=' + values[:-1]
    
    return url



def get_nwis_data(url_string, output='detailed'):
    """
    This function retrives USGS NWIS data from a specified URL, which can be 
    generated using the build_url function. 
    
    Returns: pandas DataFrame of the data
    
    Parameters
    ----------
    url_string: string
        The URL that contains the data. If the NWIS website (and not the
        build_url function) is used to generate this URL, ensure that the data
        are output in JSON format.

    output: 'detailed' (default) or 'simple'
        Detailed output will export information about the stations,
        e.g. station ID, lat, and lon. Simple output will export only variable
        values and timestamps.
    """
    #Read in data from URL
    url = urlopen(url_string)
    webdata = json.loads(url.read())
    
    #Initialize lists to hold data - can add more here as needed
    datetime_local = []
    site_id = []
    site_huc = []
    lat = []
    lon = []
    var = []
    var_code = []
    unit = []
    value = []
    
    #Some dict/list diving to extract data
    for station in webdata['value']['timeSeries']:
        datetime_local.append(station['values'][0]['value'][0]['dateTime'])
        site_id.append(station['sourceInfo']['siteCode'][0]['value'])
        site_huc.append(station['sourceInfo']['siteProperty'][1]['value'])
        lat.append(station['sourceInfo']['geoLocation']['geogLocation']['latitude'])
        lon.append(station['sourceInfo']['geoLocation']['geogLocation']['longitude'])
        var.append(station['variable']['variableName'].split(',')[0])
        var_code.append(station['variable']['variableCode'][0]['value'])
        unit.append(station['variable']['unit']['unitCode'])
        value.append(float(station['values'][0]['value'][0]['value']))
    
    #Build pandas DataFrame
    data = pd.DataFrame([datetime_local,site_id,site_huc,lat,lon,var,var_code,unit,value]).T
    data.columns = ['datetime_local','site_id','site_huc','lat','lon','var','var_code','unit','value']
    
    if output == 'simple':
        return data[['datetime_local','value']]
    else:
        return data



def gsheets_write(credentials, data, spreadsheet_title=None, 
                  email_address=None):
    """
    This function exports data to Google Sheets, either by appending the data
    to an existing spreadsheet or by creating a new one. Only one of 
    spreadsheet_title or email_address should be specified.
    
    Note that this function makes use of the gspread package. Before using this
    package, the end-user must first follow the authentication process found at
    https://gspread.readthedocs.io/en/latest/oauth2.html
    
    Returns: None
    
    Parameters
    ----------
    credentials: string
        The filename (including .json extension) of the service account 
        credentialsm for Google Sheets API. Must be a json file.
        
    data: pandas DataFrame
        The data to export.
        
    spreadsheet_title: string
        The name of an existing spreadsheet in Google Sheets to which the NWIS
        data will be appended. Note that the data will be appended to the first 
        worksheet in the file.
        
    email_address: string
        A valid email address with which the newly-created Google Sheets 
        spreadsheet will be shared.
    """
    #Check that spreadsheet name or email have been provided
    if spreadsheet_title is None and email_address is None:
        raise Exception('Enter an existing spreadsheet title or a valid email address.')
    
    if spreadsheet_title and email_address:
        raise Exception('Enter only one of spreadsheet_title or email_address.')
        
    #Set up credentials and authentication
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials, scope)
    gc = gspread.authorize(creds)
    
    #Open or create/share the spreadsheet
    if spreadsheet_title:
        sheet = gc.open(spreadsheet_title)
    else:
        sheet = gc.create('nwis_data_' + datetime.now().strftime('%Y-%m-%d_%H%M%S'))
        sheet.share(email_address, perm_type='user', role='writer')
    
    #Export data to sheet
    export_data = data.values.tolist()
    #Include column headers in new spreadsheet only
    if email_address:
        export_data.insert(0, data.columns.tolist())
        
    request_body = {'values':export_data}
    append_params = {'valueInputOption':'RAW',
                     'insertDataOption':'INSERT_ROWS',
                     'includeValuesInResponse':'FALSE',
                     'responseDateTimeRenderOption':'FORMATTED_STRING'}
    
    sheet.values_append('Sheet1', params=append_params, body=request_body)
    
    print('Data exported to Google Sheets.')
