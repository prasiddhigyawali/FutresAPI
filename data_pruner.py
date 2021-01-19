# Class for managing data that has been pruned.
# The API pruner does not attempt to fix data - instead it
# removes the data and reports it to an output file so it can be
# fixed upstream.  
import requests, zipfile, io, sys
import json
import xlrd
import pandas as pd
import urllib.request
import numpy as np
import os
import re
import configparser     
import csv
import warnings
                      
# Todo: write a function that checks for values in controlled vocabulary

# enforce numeric datatype
def datatype_pattern(value, pattern, prunedDF, df, message):
    tempDF = df
    cleanDF = df
    tempDF.loc[:, ('reason')] = message
    # convert to numeric, coerce means turn bad values to NaN
    pattern = pd.to_numeric(pattern, errors='coerce')
    # append null values to pruned result
    prunedDF = prunedDF.append(tempDF[pd.isna(pattern)])
    del tempDF['reason']

    # only accept not null values into cleanDF
    cleanDF = cleanDF[pattern.notnull()] 
    return prunedDF, cleanDF

# class that prunes matched patterns
def pattern(value, pattern, prunedDF, df, message):
    warnings.filterwarnings("ignore", 'This pattern has match groups')
    tempDF = df.copy()
    cleanDF = df.copy()
    tempDF.loc[:, ('reason')] = message
    prunedDF = prunedDF.append(tempDF[pattern.astype(str).str.contains(value) == True],ignore_index=True)
    del tempDF['reason']
    cleanDF = df[pattern.astype(str).str.contains(value) == False]
    return prunedDF, cleanDF

# loop through elements and prune
def prune_patterns(df):

    prunedDF = pd.DataFrame(columns=df.columns.values.tolist())
    
    # a very general name not useful to us
    prunedDF, df = pattern('Mammalia', df.scientificName, prunedDF, df, 'scientificName Mammalia not specific enough')
    # discard names with paranthesis
    prunedDF, df = pattern('\((.*?)\)',df.scientificName, prunedDF, df, 'scientificName has parenthesis somewhere')
    prunedDF, df = pattern('\(new SW',df.scientificName, prunedDF, df, 'scientificName matches something strange')
    prunedDF, df = pattern('whale',df.scientificName, prunedDF, df, 'scientificName whale not parseable')
    # remove completely empty names
    prunedDF, df = pattern('^\s*$',df.scientificName, prunedDF, df, 'scientificName is completely empty')
    prunedDF, df = pattern(chr(34),df.scientificName, prunedDF, df, 'scientificName has a quote somewhere')
    # contains more than one space together
    prunedDF, df = pattern('  ',df.scientificName, prunedDF, df, 'scientificName has two spaces together')
    # do not want stray quotations
    prunedDF, df = pattern('"',df.scientificName, prunedDF, df, 'scientificName has a quote')
    prunedDF, df = pattern('\'',df.scientificName, prunedDF, df, 'scientificName has a quote')
    # remove names with commans
    prunedDF, df = pattern(',',df.scientificName, prunedDF, df, 'scientificName has a comma')
    # no question marks in names
    prunedDF, df = pattern('\?',df.scientificName, prunedDF, df, 'scientificName has a question mark')
    # this fails because the column has numbers
    prunedDF, df = pattern('\-\-',df.measurementValue, prunedDF, df, 'measurementValue -- is invalid')
    prunedDF, df = datatype_pattern('',df.measurementValue, prunedDF, df, 'measurementValue not a float')
          
    cleanDF = df                
    return prunedDF, cleanDF

def init(df):
    print ('pruning')
    prunedDF, cleanDF = prune_patterns(df)
    return prunedDF, cleanDF

def testit():
    temp_file = "test.xlsx"
    df = pd.read_excel(temp_file,sheet_name='Samples', na_filter=False)  
    prunedDF, cleanDF = init(df) 
    prunedDF.to_csv(temp_file + '.pruned.csv', index=False)   
    cleanDF.to_csv(temp_file + '.clean.csv', index=False)
    
    
    print ("*******************")
    print ("clean data:")
    print ("*******************")
    print (cleanDF)
    print ("*******************")
    print ("pruned data:")
    print ("*******************")
    print (prunedDF)

testit()
