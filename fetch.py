import requests, zipfile, io, sys
import json
import xlrd
import pandas as pd
import urllib.request
import numpy as np
import os
import re
import configparser     
        
# hold scientificName objects 
class scientificNames:
    def __init__(self, name):  
        self.name = name  
        self.projects = list()
    def add_project(self, projectCounter):
        self.projects.append(projectCounter) 
        
class projectCounter:
    def __init__(self, projectId, count):  
        self.projectId = projectId
        self.count = count
                         
def quicktest():
    temp_file = "test.xlsx"
    print ('processing ' + temp_file)

    df = pd.read_excel(temp_file,sheet_name='Samples', na_filter=False)                                                    
    df = taxonomize(df)
        
    group = df.groupby('scientificName')['scientificName'].size()    
    json_writer(group,'scientificName','data/scientificName.json','counts grouped by scientificName') 
    
    group = df.groupby('scientificName')['scientificName'].value_counts().sort_values(ascending=False).head(20)            
    json_writer(group,'scientificName','data/scientificName_top20.json','counts grouped by scientificName for top 20 names') 
    
    
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
            
            url="https://api.geome-db.org/records/Event/excel?networkId=1&q=_projects_:" + str(project["projectId"]) + "+_select_:%5BSample,Diagnostics%5D" + "&access_token="+access_token
            r = requests.get(url)
            if (r.status_code == 204):
                print ('no data found for project = ' + str(project["projectId"]))
            else:
                print("processing data for project = " + str(project["projectId"]))
                temp_file = 'data/project_' + str(project["projectId"]) + ".xlsx"                                                
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
                #thisDF['projectURL'] = str("https://geome-db.org/workbench/project-overview?projectId=") + thisDF['projectId'].astype(str)
                # Remove bad measurementValues
                thisDF = thisDF[thisDF.measurementValue != '--']   
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
                thisDF['projectId'] = 'Vertnet'
                # create empty columns for genus/specificEpithet, we will use scientificName to 
                # parse these in taxonomize functon
                thisDF['genus'] = ''
                thisDF['specificEpithet'] = ''
                thisDF = thisDF[columns] 
                      
                thisDF = thisDF.reindex(columns=columns)            
                thisDF = thisDF.astype(str)
                # Remove bad measurementValues
                thisDF = thisDF[thisDF.measurementValue != '--']   
                df = df.append(thisDF,sort=False)  
    
    df = taxonomize(df);

    print("writing dataframe to spreadsheet and zipped csv file...")               
    # Create a compressed output file so people can view a limited set of columns for the complete dataset
    SamplesDFOutput = df.reindex(columns=columns)
    SamplesDFOutput.to_csv(processed_csv_filename_zipped, index=False, compression="gzip")                  

def taxonomize(df):
    print ("cleaning up taxonomy")
    df['scientificName'] = df['scientificName'].str.replace('cf.','')    
    df['scientificName'] = df['scientificName'].str.replace('cf','')
    df['scientificName'] = df['scientificName'].str.replace('sp.','')
    df['scientificName'] = df['scientificName'].str.replace('sp','')
    df['scientificName'] = df['scientificName'].str.replace('aff.','')
    df['scientificName'] = df['scientificName'].str.replace('\(new SW','')
    df['scientificName'] = df['scientificName'].str.replace('whale','')
    df['scientificName'] = df['scientificName'].str.replace('unknown','')

    # remove all material between parenthesis and the paranthesis themselves
    df['scientificName'] = df['scientificName'].str.replace("\((.*?)\)",'')  
    df['scientificName'] = df['scientificName'].str.strip()
    df['scientificName'] = df['scientificName'].str.replace('  ',' ')
    # If so much as see a question mark, call the name Unknown
    df['scientificName'] = df['scientificName'].apply(lambda x: 'Unknown' if '?' in x else x)
    # limit to binomial.  do not need trinomials or more
    df['scientificName'] = df.apply(lambda x: ' '.join(x['scientificName'].split()[:2]), axis=1)
    df['scientificName'] = df['scientificName'].str.replace(chr(34),'')
    # if scientificName is completely empty we call it Unknown
    df['scientificName'] = df['scientificName'].str.replace(r'^\s*$','Unkown')
    df['genus'] = df['scientificName'].str.split(' ').str[0]
    df['specificEpithet'] = df['scientificName'].str.split(' ').str[1]
    df['specificEpithet'] = df['specificEpithet'].fillna('')

    

    return df    
    
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
def json_tuple_writer_scientificName_projectId(group,name):
    projectId = ''
    thisprojectId = ''
    jsonstr = ''
    firsttime = True
    for rownum,(indx,val) in enumerate(group.iteritems()):  
        #print(str(indx[0]),str(indx[1]), str(val))              
        thisprojectId = str(indx[0])
        if (projectId != thisprojectId):
            # End of file
            if firsttime == False:                
                jsonstr = jsonstr.rstrip(',\n')
                jsonstr += "\n]"            
                with open('data/scientificName_projectId_' + projectId + ".json",'w') as f:
                    f.write(jsonstr)                      
            # Beginning of file
            jsonstr = "[\n"
            jsonstr += ("\t{\"scientificName\":\"" + str(indx[1]) + "\",\"value\":"+str(val) +"},\n" )

            api.write("|data/scientificName_projectId_"+thisprojectId +".json|unique scientificName count for project "+thisprojectId+"|\n")                
        else:                                    
            jsonstr += ("\t{\"scientificName\":\"" + str(indx[1]) + "\",\"value\":"+str(val) +"},\n" )

            
        projectId = thisprojectId

        
        firsttime = False            
    
    # write the last one
    jsonstr = jsonstr.rstrip(',\n')
    jsonstr += "\n]"
    with open('data/scientificName_projectId_' + thisprojectId +".json",'w') as f:
                f.write(jsonstr)        
         
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
        projectId = str(indx[1])
        count = str(val)                              
        if (scientificName != thisscientificName): 
            if firsttime:
                s = scientificNames(thisscientificName)             
                s.add_project(projectCounter(projectId,count)) 
            else:    
                scientificNameList.append(s)
                s = scientificNames(thisscientificName)       
                s.add_project(projectCounter(projectId,count))                                                       
        else:
            s.add_project(projectCounter(projectId,count))         
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
            jsonstr += ("{\"projectId\" : \"" + project.projectId + "\" , \"count\" : " + project.count  + "},")
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
            projectId =  str(project["projectId"])
            projectTitle = str(project["projectTitle"])
            principalInvestigator  = str(project["principalInvestigator"])
            principalInvestigatorAffiliation = str(project['principalInvestigatorAffiliation'])
            public = str(project["public"])
            discoverable  = str(project["discoverable"])
            diagnosticsCount = project["entityStats"]["DiagnosticsCount"]
            jsonstr += "\"projectId\" : \"" + projectId + "\", "
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
    jsonstr += "\"projectId\" : \"Vertnet\", "
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
    json_writer(group,'measurementType','data/measurementType.json','measuremenType')    
    
    # scientificName by projectId
    group = df.groupby(['projectId','scientificName']).size()
    json_tuple_writer_scientificName_projectId(group,'projectId')
    
    # scientificName listing
    group = df.groupby(['scientificName','projectId']).size()
    json_tuple_writer_scientificName_listing(group,'scientificName',df)


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
columns = ['materialSampleID','country','locality','yearCollected','samplingProtocol','basisOfRecord','scientificName','genus','specificEpithet','measurementMethod','measurementUnit','measurementType','measurementValue','lifeStage','individualID','sex','decimalLatitude','decimalLongitude','projectId']
processed_csv_filename_zipped = 'data/futres_data_processed.csv.gz'

# Setup initial Environment
parser = configparser.ConfigParser()
if os.path.exists("db.ini") == False:
    print("unable fo read db.ini file, try copying dbtemp.ini to db.ini and updating setttings")
    sys.exit()
  
parser.read('db.ini')  

# geomedb variables
host = parser.get('geomedb', 'url')
user = parser.get('geomedb', 'username')
passwd = parser.get('geomedb', 'password')
futres_team_id = parser.get('geomedb', 'futres_team_id')
# TODO: dynamically fetch access_token
access_token = parser.get('geomedb', 'access_token')

# Run Application
#quicktest()

#fetch_geome_data()
project_table_builder()
process_data()
df = read_processed_data()
group_data(df)

# Finish up
api.close()
