
import requests, zipfile, io, sys
import json
import xlrd
import pandas as pd
import urllib.request
import numpy as np

# hold scientificName objects which 
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

# fetch data from GEOME that matches the Amphibian Disease TEAM and put into an easily queriable format.
def fetch_data():
    print("fetching data...")
    # populate proejcts array with a complete list of project IDs 
    # for the amphibianDiseaseTeam
    futresTeamID = 70   
    df = pd.DataFrame(columns = columns)
     
    # this will fetch a list of ALL projects from GEOME        
    # TODO: dynamically fetch access_token
    access_token = "k-vdVfvh2qDeC8JBekce"    
    url = "https://api.geome-db.org/projects?includePublic=false&access_token="+access_token    
    r = requests.get(url)
    print(url)
    for project in json.loads(r.content):
        projectConfigurationID = project["projectConfiguration"]["id"]
        # filter for just projects matching the teamID
        print (projectConfigurationID)
        if (projectConfigurationID == futresTeamID):
            
            url="https://api.geome-db.org/records/Event/excel?networkId=1&q=_projects_:" + str(project["projectId"]) + "+_select_:%5BSample,Diagnostics%5D" + "&access_token="+access_token
            r = requests.get(url)
            if (r.status_code == 204):
                print ('no data found for project = ' + str(project["projectId"]))
            else:
                print("processing data for project = " + str(project["projectId"]))
                temp_file = 'data/project' + str(project["projectId"]) + ".xlsx"                                                
                excel_file_url = json.loads(r.content)['url']   + "?access_token=" + access_token             
                reqRet = urllib.request.urlretrieve(excel_file_url, temp_file)
                
                thisDF = pd.read_excel(temp_file,sheet_name='Samples', na_filter=False)                                
                thisDF = thisDF.reindex(columns=columns)            
                thisDF = thisDF.astype(str)
                thisDF['projectURL'] = str("https://geome-db.org/workbench/project-overview?projectId=") + thisDF['projectId'].astype(str)
                # TODO: remove this when GEOME data has been sanitized
                thisDF = thisDF[thisDF.measurementValue != '--']
   
                df = df.append(thisDF,sort=False)
     
    print("writing final data...")            
    # write to an excel file, used for later processing
    df.to_excel(processed_filename,index=False)    
    # Create a compressed output file so people can view a limited set of columns for the complete dataset
    SamplesDFOutput = df.reindex(columns=columns)
    SamplesDFOutput.to_csv(processed_csv_filename_zipped, index=False, compression="gzip")                                            

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
        jsonstr+="\""+name+"\":\""+str(val[0])+"\","            
        jsonstr+="\"value\":"+str(val[1])  
        jsonstr+="},\n"                   
        
        
    jsonstr = jsonstr.rstrip(',\n')
    jsonstr += '\n]'
    with open(filename,'w') as f:
        f.write(jsonstr)

    
def group_data():  
    print("reading processed data ...")
    df = pd.read_excel(processed_filename)
    
    print("grouping results ...")    
    
    group = df.groupby('scientificName')['scientificName'].size()    
    json_writer(group,'scientificName','data/scientificName.json','counts grouped by scientificName') 
    
    group = df.groupby('country')['country'].size()    
    json_writer(group,'country','data/country.json','counts grouped by country') 
    
    group = df.groupby('yearCollected')['yearCollected'].size()    
    json_writer(group,'yearCollected','data/yearCollected.json','counts grouped by yearCollected') 
    
    group = df.groupby('measurementType')['measurementType'].size()
    json_writer(group,'measurementType','data/measurementType.json','measuremenType')    
    
    # scientificName by projectId
    group = df.groupby(['projectId','scientificName']).size()
    json_tuple_writer_scientificName_projectId(group,'projectId')
    
    # scientificName listing
    group = df.groupby(['scientificName','projectId']).size()
    json_tuple_writer_scientificName_listing(group,'scientificName',df)

api = open("api.md","w")
api.write("# API\n\n")
api.write("Amphibian Disease Portal API Documentation\n")
api.write("|filename|definition|\n")
api.write("|----|---|\n")

# global variables
columns = ['materialSampleID','country','locality','yearCollected','samplingProtocol','basisOfRecord','scientificName','measurementMethod','measurementUnit','measurementType','measurementValue','lifeStage','individualID','sex','decimalLatitude','decimalLongitude','projectId']
processed_filename = 'data/futres_data_processed.xlsx'
processed_csv_filename_zipped = 'data/futres_data_processed.csv.gz'

#fetch_data()
group_data()

api.close()