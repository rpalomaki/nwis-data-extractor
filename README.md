# nwis-data-extractor

A small package to download USGS/NWIS data and export to Google Sheets. Also stores the data in a pandas DataFrame for further analysis in python.

## Dependencies
- [pandas](https://pandas.pydata.org/)
- [gspread](https://github.com/burnash/gspread) - Google Sheets Python API
  - This package requires some [initial setup and authentication](https://gspread.readthedocs.io/en/latest/oauth2.html).
  
## Examples

### Generating NWIS URL
```python
import nwis_data_extractor as nde

#Select stations, e.g. using hydrologic unit codes (huc), and desired variables
huc = [17070201,17070202,17070203,17070204]
var = ['00060','00065']
#Build URL
url = nde.build_url(huc=huc, variable=var)
```

### Extracting data
```python
webdata = nde.get_nwis_data(url) #Detailed output
simple_data = nde.get_nwis_data(url, output='simple') #Timestamps and values only
```

### Exporting data to Google Sheets
```python
creds = 'my_credentials.json' #Obtained through gspread directions
my_sheet = 'existing_spreadsheet' #Sheet title on Google Drive
my_email = 'name@address.org'

#Exporting to an existing spreadsheet in the user's Google Drive
nde.gsheets_write(credentials=creds, data=webdata, spreadsheet_title=my_sheet)
#Exporting to a new spreadsheet, which will be shared with the user's email address
nde.gsheets_write(credentials=creds, data=simple_data, email_address=my_email)
```

## Additional resources
- [NWIS URL generation tool](https://waterservices.usgs.gov/rest/IV-Test-Tool.html)
- [List of NWIS URL arguments](https://waterservices.usgs.gov/rest/IV-Service.html#URLFormat)
- [List of NWIS Hydrologic Unit Codes](https://water.usgs.gov/GIS/huc_name.html)
