import requests, zipfile, io, sys
import json
import xlrd
import pandas as pd
import urllib.request
import numpy as np
import os
import re
from configparser import ConfigParser
import data_pruner
        
# hold scientificName objects 
class scientificNames:
    def __init__(self, name):  
        self.name = name  
        self.projects = list()
    def add_project(self, projectCounter):
        self.projects.append(projectCounter) 
        
class projectCounter:
    def __init__(self, projectID, count):  
        self.projectID = projectID
        self.count = count
                         
def quicktest():
    temp_file = "test.xlsx"
    print ('processing ' + temp_file)

    df = pd.read_excel(temp_file,sheet_name='Samples', na_filter=False)                                                    
    prunedDF, cleanDF = data_cleaning(df)
     
    #print(prunedDF)
    print(cleanDF[['materialSampleID','measurementValue','measurementUnit','yearCollected']])
    #group = cleanDF.groupby('scientificName')['scientificName'].size()    
    #json_writer(group,'scientificName','data/scientificName.json','counts grouped by scientificName') 
    
    #group = cleanDF.groupby('scientificName')['scientificName'].value_counts().sort_values(ascending=False).head(20)            
    #json_writer(group,'scientificName','data/scientificName_top20.json','counts grouped by scientificName for top 20 names') 
    
    
# fetch data from GEOME that matches the Futres TEAM and put into an easily queriable format.
def fetch_geome_data():
    print("fetching data...")
    # populate proejcts array with a complete list of project IDs for this team
    #df = pd.DataFrame(columns = columns)
     
    # this will fetch a list of ALL projects from GEOME          
    url = "https://api.geome-db.org/projects?includePublic=false&access_token="+access_token    
    r = requests.get(url)
    print("fetching " + url)

    for project in json.loads(r.content):
        projectConfigurationID = project["projectConfiguration"]["id"]
        # filter for just projects matching the teamID
        if (str(projectConfigurationID) == str(futres_team_id)):
            
            url="https://api.geome-db.org/records/Event/excel?networkId=1&q=_projects_:" + str(project["projectID"]) + "+_select_:%5BSample,Diagnostics%5D" + "&access_token="+access_token
            r = requests.get(url)
            if (r.status_code == 204):
                print ('no data found for project = ' + str(project["projectID"]))
            else:
                print("processing data for project = " + str(project["projectID"]))
                temp_file = 'data/project_' + str(project["projectID"]) + ".xlsx"                                                
                excel_file_url = json.loads(r.content)['url']   + "?access_token=" + access_token             
                reqRet = urllib.request.urlretrieve(excel_file_url, temp_file)                
                                                                  
def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1
                
def process_data():
    df = pd.DataFrame(columns = columns)

    # look in data directory for all files called project_*.xlsx
    print ('processing GEOME data...')    
    for subdir, dirs, files in os.walk('data'):
        for file in files:
            ext = os.path.splitext(file)[-1].lower()        
            prefix = os.path.splitext(file)[0].split("_")[0]            
            
            if ext == ".xlsx" and prefix == "project":
                temp_file = os.path.join(subdir, file)
                print ('processing ' + temp_file)

                thisDF = pd.read_excel(temp_file,sheet_name='Samples', na_filter=False)                                                
                thisDF = thisDF.reindex(columns=columns)            
                thisDF = thisDF.astype(str)
                df = df.append(thisDF,sort=False)
    
    print ('processing Vertnet data...')  
    for subdir, dirs, files in os.walk('vertnet'):
        for file in files:
            ext = os.path.splitext(file)[-1].lower()        
            prefix = os.path.splitext(file)[0].split("_")[0]            
            
            if ext == ".csv" and prefix == "FuTRES":                
                temp_file = os.path.join(subdir, file)
                print ('processing ' + temp_file)
                thisDF = pd.read_csv(temp_file, na_filter=False)                                                
                thisDF['individualID'] = ''
                thisDF['observationID'] = ''

                thisDF['projectID'] = 'Vertnet'
                # create empty columns for genus/specificEpithet, we will use scientificName to 
                # parse these in taxonomize functon
                thisDF['genus'] = ''
                thisDF['specificEpithet'] = ''
                thisDF = thisDF[columns] 
                      
                thisDF = thisDF.reindex(columns=columns)            
                thisDF = thisDF.astype(str)

                df = df.append(thisDF,sort=False)  
    
    prunedDF, cleanDF = data_cleaning(df)
    
    print("writing dataframe to spreadsheet and zipped csv file...")               
    # Create a compressed output file so people can view a limited set of columns for the complete dataset
    SamplesDFOutput = cleanDF.reindex(columns=columns)
    SamplesDFOutput.to_csv(processed_csv_filename_zipped, index=False, compression="gzip")
    
    prunecolumns = columns
    prunecolumns.append('reason')
    PrunedDFOutput = prunedDF.reindex(columns=prunecolumns)
    PrunedDFOutput.to_csv(pruned_csv_filename, index=False)

# Final step of data cleaning
# we are careful about what values we change here... we only change
# things that are straightforward, such as changing cases, and converting
# values.  The data_pruner is used to report & toss data that is unclear (e.g. names with ?)
def data_cleaning(df):
    # reset indexes
    df = df.reindex(columns=columns)    
    df = df.reset_index(drop=True)
    
    df['genus'] = df['scientificName'].str.split(' ').str[0]
    df['specificEpithet'] = df['scientificName'].str.split(' ').str[1]    
    
    # standardize yearCollected values
    df.loc[df['yearCollected'] == 'Unknown', 'yearCollected'] = 'unknown'
    #df.loc[df['yearCollected'] == 'unknown', 'yearCollected'] = ''
    #df['yearCollected'] = df['yearCollected'].astype(str).astype(int,errors='ignore')

    # create an observationID as unique value based on row index
    df["observationID"] = df.index + 1
    # the curly braces are used by the pipeline code to interpret rdfs:label values
    df["measurementType"] = '{' + df['measurementType'].astype(str) + '}'    
    
    # Run pruner
    prunedDF, cleanDF = data_pruner.init(df)
    
    # convert all measurement units that are available in GEOME to either mm or g
    # length
    cleanDF.loc[cleanDF['measurementUnit'] == 'in', 'measurementValue'] = cleanDF.measurementValue.astype(float) * 25.4
    cleanDF.loc[cleanDF['measurementUnit'] == 'in', 'measurementUnit'] = 'mm'
    cleanDF.loc[cleanDF['measurementUnit'] == 'cm', 'measurementValue'] = cleanDF.measurementValue.astype(float) * 10
    cleanDF.loc[cleanDF['measurementUnit'] == 'cm', 'measurementUnit'] = 'mm'
    cleanDF.loc[cleanDF['measurementUnit'] == 'm', 'measurementValue'] = cleanDF.measurementValue.astype(float) * 1000
    cleanDF.loc[cleanDF['measurementUnit'] == 'm', 'measurementUnit'] = 'mm'
    cleanDF.loc[cleanDF['measurementUnit'] == 'ft', 'measurementValue'] = cleanDF.measurementValue.astype(float) * 304.8
    cleanDF.loc[cleanDF['measurementUnit'] == 'ft', 'measurementUnit'] = 'mm'
    cleanDF.loc[cleanDF['measurementUnit'] == 'km', 'measurementValue'] = cleanDF.measurementValue.astype(float) * 1000000
    cleanDF.loc[cleanDF['measurementUnit'] == 'km', 'measurementUnit'] = 'mm'
    # weight
    cleanDF.loc[cleanDF['measurementUnit'] == 'kg', 'measurementValue'] = cleanDF.measurementValue.astype(float) * 1000
    cleanDF.loc[cleanDF['measurementUnit'] == 'kg', 'measurementUnit'] = 'g'
    cleanDF.loc[cleanDF['measurementUnit'] == 'lb', 'measurementValue'] = cleanDF.measurementValue.astype(float) * 453.592
    cleanDF.loc[cleanDF['measurementUnit'] == 'lb', 'measurementUnit'] = 'g'
    cleanDF.loc[cleanDF['measurementUnit'] == 'oz', 'measurementValue'] = cleanDF.measurementValue.astype(float) * 28.3495
    cleanDF.loc[cleanDF['measurementUnit'] == 'oz', 'measurementUnit'] = 'g'
        
    return prunedDF, cleanDF
        
# function to write tuples to json from pandas group by
# using two group by statements.
def json_tuple_writer(group,name,filename,definition):
    api.write("|"+filename+"|"+definition+"|\n")
    jsonstr = '[\n'
    namevalue = ''
    for rownum,(indx,val) in enumerate(group.iteritems()):                
        
        thisnamevalue = str(indx[0])
        
        if (namevalue != thisnamevalue):
            jsonstr+="\t{"
            jsonstr+="\""+name+"\":\""+thisnamevalue+"\","
            jsonstr+="\""+str(indx[1])+"\":"+str(val)  
            jsonstr+="},\n"                   
        else:
            jsonstr = jsonstr.rstrip("},\n")
            jsonstr+=",\""+str(indx[1])+"\":"+str(val)  
            jsonstr+="},\n"                           
        
        namevalue = thisnamevalue                
        
    jsonstr = jsonstr.rstrip(',\n')

    jsonstr += '\n]'
    with open(filename,'w') as f:
        f.write(jsonstr)
        
        
# function to write tuples to json from pandas group by
# using two group by statements.
def json_tuple_writer_scientificName_projectID(group,name):
    projectID = ''
    thisprojectID = ''
    jsonstr = ''
    firsttime = True
    for rownum,(indx,val) in enumerate(group.iteritems()):  
        #print(str(indx[0]),str(indx[1]), str(val))              
        thisprojectID = str(indx[0])
        if (projectID != thisprojectID):
            # End of file
            if firsttime == False:                
                jsonstr = jsonstr.rstrip(',\n')
                jsonstr += "\n]"            
                with open('data/scientificName_projectID_' + projectID + ".json",'w') as f:
                    f.write(jsonstr)                      
            # Beginning of file
            jsonstr = "[\n"
            jsonstr += ("\t{\"scientificName\":\"" + str(indx[1]) + "\",\"value\":"+str(val) +"},\n" )

            api.write("|data/scientificName_projectID_"+thisprojectID +".json|unique scientificName count for project "+thisprojectID+"|\n")                
        else:                                    
            jsonstr += ("\t{\"scientificName\":\"" + str(indx[1]) + "\",\"value\":"+str(val) +"},\n" )

            
        projectID = thisprojectID

        
        firsttime = False            
    
    # write the last one
    jsonstr = jsonstr.rstrip(',\n')
    jsonstr += "\n]"
    with open('data/scientificName_projectID_' + thisprojectID +".json",'w') as f:
                f.write(jsonstr)        
         
         
# function to write tuples to json from pandas group by
# using two group by statements.
def json_tuple_writer_scientificName_measurementType(group,name):
    csvstr = ''
    for rownum,(indx,val) in enumerate(group.iteritems()):               
        thisSciName = str(indx[0])
        thisMeasurementType = str(indx[1])
        thisVal = str(val)
        csvstr += thisSciName +","+thisMeasurementType+","+thisVal +"\n"
    with open('data/scientificNameMeasurementType.csv','w') as f:
        f.write(csvstr) 
        
                 
# Create a file for each scientificName listing the projects that it occurs in.
def json_tuple_writer_scientificName_listing(group,name,df):
    scientificName = ''
    thisscientificName = ''
    jsonstr = ''
    firsttime = True
    scientificNameList = list()
    s = scientificNames('')
    
    # loop all grouped names & projects and populate list of objects
    # from these we will construct JSONS downstream
    for rownum,(indx,val) in enumerate(group.iteritems()):          
        thisscientificName = str(indx[0])
        projectID = str(indx[1])
        count = str(val)                              
        if (scientificName != thisscientificName): 
            if firsttime:
                s = scientificNames(thisscientificName)             
                s.add_project(projectCounter(projectID,count)) 
            else:    
                scientificNameList.append(s)
                s = scientificNames(thisscientificName)       
                s.add_project(projectCounter(projectID,count))                                                       
        else:
            s.add_project(projectCounter(projectID,count))         
        scientificName = thisscientificName    
        firsttime = False    

    # construct JSON output
    # TODO: we have a df object accessible here, so we can lookup species information that we fetched.
    # an example of what this looks like:
    # myfilter = df.query('scientificName==\"'+sciName.name+'\"',inplace=False)       
    # print(myfilter['family'].iloc[0] + ":" + sciName.name)
    jsonstr = ("[\n")
    for sciName in scientificNameList:                
        jsonstr += ("\t{\"scientificName\" : \"" + sciName.name + "\" , \"associatedProjects\" : [" )
        for project in sciName.projects:
            jsonstr += ("{\"projectID\" : \"" + project.projectID + "\" , \"count\" : " + project.count  + "},")
        jsonstr = (jsonstr.rstrip(','))        
        jsonstr += ("]},\n")
    jsonstr = (jsonstr.rstrip(',\n'))        
    jsonstr += ("]")
                
    with open('data/scientificName_listing.json','w') as f:
        f.write(jsonstr) 
    api.write("|scientificName_listing.json|All scientific names and the projects that they appear in|\n")
        
# function to write JSON from pandas groupby
def json_writer(group,name,filename,definition):    
    api.write("|"+filename+"|"+definition+"|\n")
    jsonstr = '[\n'
    for (rownum,val) in enumerate(group.iteritems()):                        
        jsonstr+="\t{"
        # if type comes through as tuple here just take first element
        if type(val[0]) is tuple:
            jsonstr+="\""+name+"\":\""+str(val[0][0])+"\","            
        else:
            jsonstr+="\""+name+"\":\""+str(val[0])+"\","            
        jsonstr+="\"value\":"+str(val[1])  
        jsonstr+="},\n"                           
        
    jsonstr = jsonstr.rstrip(',\n')
    jsonstr += '\n]'
    with open(filename,'w') as f:
        f.write(jsonstr)

# fetch data from GEOME that matches the Futres TEAM and put into an easily queriable format.
def project_table_builder():    
    print("building project table...")
    filename = 'data/projects.json'
    public = True
    discoverable = True
    api.write("|"+filename+"|display project data|\n")
    # populate proejcts array with a complete list of project IDs for this team
    # this will fetch a list of ALL projects from GEOME        
    url = "https://api.geome-db.org/projects/stats?includePublic=false&access_token="+access_token    
    r = requests.get(url)
    jsonstr = "["
    for project in json.loads(r.content):
        projectConfigurationID = project["projectConfiguration"]["id"]
        # filter for just projects matching the teamID  
        if (str(projectConfigurationID) == str(futres_team_id)):     
            jsonstr += "\n\t{"           
            projectID =  str(project["projectID"])
            projectTitle = str(project["projectTitle"])
            principalInvestigator  = str(project["principalInvestigator"])
            principalInvestigatorAffiliation = str(project['principalInvestigatorAffiliation'])
            public = str(project["public"])
            discoverable  = str(project["discoverable"])
            diagnosticsCount = project["entityStats"]["DiagnosticsCount"]
            jsonstr += "\"projectID\" : \"" + projectID + "\", "
            jsonstr += "\"projectTitle\" : \"" + projectTitle + "\", "
            jsonstr += "\"principalInvestigator\" : \"" + principalInvestigator + "\", "
            jsonstr += "\"principalInvestigatorAffiliation\" : \"" + principalInvestigatorAffiliation + "\", "
            jsonstr += "\"public\" : \"" + public + "\", "
            jsonstr += "\"discoverable\" : \"" + discoverable + "\", "
            jsonstr += "\"entityStats\": {\"DiagnosticsCount\" : " + str(diagnosticsCount) + "}"
            jsonstr += "},"
    
    # count records in vertnet data
    # each line in vertnet directory is a measurement, count number of lines in files
    len = 0
    for subdir, dirs, files in os.walk('vertnet'):        
        for file in files:
            ext = os.path.splitext(file)[-1].lower()        
            prefix = os.path.splitext(file)[0].split("_")[0]            
            
            if ext == ".csv" and prefix == "FuTRES":                 
                len += file_len('vertnet/'+file)
    
    jsonstr += "\n\t{"           
    jsonstr += "\"projectID\" : \"Vertnet\", "
    jsonstr += "\"projectTitle\" : \"VertNet\", "
    jsonstr += "\"principalInvestigator\" : \"\", "
    jsonstr += "\"principalInvestigatorAffiliation\" : \"\", "
    jsonstr += "\"public\" : \"True\", "
    jsonstr += "\"discoverable\" : \"True\", "
    jsonstr += "\"entityStats\": {\"DiagnosticsCount\" : " + str(len) + "}"
    jsonstr += "}"    
    jsonstr += "\n]"
    
    with open(filename,'w') as f:
        f.write(jsonstr)

def read_processed_data():
    print("reading processed data ...")
    return pd.read_csv(processed_csv_filename_zipped)
    
def group_data(df):      
    print("grouping results ...")    
    
    group = df.groupby('scientificName')['scientificName'].size()    
    json_writer(group,'scientificName','data/scientificName.json','counts grouped by scientificName') 
    
    group = df.groupby('scientificName')['scientificName'].value_counts().sort_values(ascending=False).head(20)            
    json_writer(group,'scientificName','data/scientificName_top20.json','counts grouped by scientificName for top 20 names') 
              
    group = df.groupby('country')['country'].size()    
    json_writer(group,'country','data/country.json','counts grouped by country') 
    
    group = df.groupby('country')['country'].value_counts().sort_values(ascending=False).head(20)            
    json_writer(group,'country','data/country_top20.json','counts grouped by country for top 20 names') 
    
    group = df.groupby('yearCollected')['yearCollected'].size()    
    json_writer(group,'yearCollected','data/yearCollected.json','counts grouped by yearCollected') 
    
    group = df.groupby('measurementUnit')['measurementUnit'].size()
    json_writer(group,'measurementUnit','data/measurementUnit.json','counts grouped by measurementUnit')

    group = df.groupby('measurementType')['measurementType'].size()
    json_writer(group,'measurementType','data/measurementType.json','measurementType')    
    
    # scientificName by projectID
    group = df.groupby(['projectID','scientificName']).size()
    json_tuple_writer_scientificName_projectID(group,'projectID')
    
    # scientificName listing
    group = df.groupby(['scientificName','projectID']).size()
    json_tuple_writer_scientificName_listing(group,'scientificName',df)

    # measurementType/scientificName
    group = df.groupby(['scientificName','measurementType']).size()
    json_tuple_writer_scientificName_measurementType(group,'scientificName')

######################################################
# Run Application Code
######################################################
# Require minimum python version
MIN_PYTHON = (3, 6)
if sys.version_info < MIN_PYTHON:
    sys.exit("Python %s.%s or later is required.\n" % MIN_PYTHON)
    
# Setup API output
api = open("api.md","w")
api.write("# API\n\n")
api.write("Futres API Documentation\n")
api.write("|filename|definition|\n")
api.write("|----|---|\n")

# global variables
columns = ['observationID','materialSampleID','country','locality','yearCollected','samplingProtocol','basisOfRecord','scientificName','genus','specificEpithet','measurementMethod','measurementUnit','measurementType','measurementValue','lifeStage','individualID','sex','decimalLatitude','decimalLongitude','projectID']
processed_csv_filename_zipped = 'data/futres_data_processed.csv.gz'
pruned_csv_filename = 'data/futres_data_with_errors.csv'


# Setup initial Environment
parser = ConfigParser()
if os.path.exists("db.ini") == False:
    print("unable fo read db.ini file, try copying dbtemp.ini to db.ini and updating setttings")
    sys.exit()
parser = ConfigParser()
parser.read('db.ini')
# information to grab access_token from GEOME
futres_team_id = parser.get('geomedb', 'futres_team_id')
host = parser.get('geomedb', 'url')
user = parser.get('geomedb', 'Username')
passwd = parser.get('geomedb', 'Password')
token_url = parser.get('geomedb', 'accessToken_url')
url = requests.get(token_url)
payload = {'client_id':parser.get('geomedb', 'client_id'),
        'grant_type':parser.get('geomedb', 'grant_type'),
        'username': user,
        'password':passwd}
res = requests.post(token_url, data = payload)
access_token = res.json()["access_token"]

# Run Application
#quicktest()

fetch_geome_data()
project_table_builder()
process_data()
df = read_processed_data()
group_data(df)

## Finish up
api.close()
