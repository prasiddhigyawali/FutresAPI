# Class for managing data that has been pruned.
# Important that the API parser does not attempt to fix data.
# it instead just removes the data and reports it so it can be
# fixed upstream.  To this end, we write all pruned data out to 
# a "pruned" data file
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



# parser class which we use to manage data that is pruned
# prunedDF listing value that was pruned
# df missing the pruned value
def parser(value, pattern, prunedDF, df, message):
    warnings.filterwarnings("ignore", 'This pattern has match groups')
    df['reason'] = message
    prunedDF = prunedDF.append(df[pattern.str.contains(value) ],ignore_index=True)
    del df['reason']
    df = df[~pattern.str.contains(value) ]
    return prunedDF, df

# loop through elements and prune
def prune_patterns(df):

    prunedDF = pd.DataFrame(columns=df.columns.values.tolist())
    
    # a very general name not useful to us
    prunedDF, df = parser('Mammalia', df.scientificName, prunedDF, df, 'scientificName cannot match Mammalia')
    # discard names with paranthesis
    prunedDF, df = parser('\((.*?)\)',df.scientificName, prunedDF, df, 'scientificName has parenthesis somewhere')
    prunedDF, df = parser('\(new SW',df.scientificName, prunedDF, df, 'scientificName matches something strange')
    prunedDF, df = parser('whale',df.scientificName, prunedDF, df, 'scientificName not specific enough')
    # remove completely empty names
    prunedDF, df = parser('^\s*$',df.scientificName, prunedDF, df, 'scientificName is completely empty')
    prunedDF, df = parser(chr(34),df.scientificName, prunedDF, df, 'scientificName has a quote somewhere')
    # contains more than one space together
    prunedDF, df = parser('  ',df.scientificName, prunedDF, df, 'scientificName has two spaces together')
    # do not want stray quotations
    prunedDF, df = parser('"',df.scientificName, prunedDF, df, 'scientificName has a quote')
    prunedDF, df = parser('\'',df.scientificName, prunedDF, df, 'scientificName has a quote')
    # remove names with commans
    prunedDF, df = parser(',',df.scientificName, prunedDF, df, 'scientificName has a comma')
    # no question marks in names
    prunedDF, df = parser('\?',df.scientificName, prunedDF, df, 'scientificName has a question mark')

            
    return prunedDF, df

def testit():
    data = {'scientificName':  
        ['Mammalia', 'Lynx rufus','(new SW','','some name?','Foo"']
        }
            
    df = pd.DataFrame (data, columns = ['scientificName'])
    prunedDF, df = prune_patterns(df)
    prunedDF.to_csv('data/pruned.csv', index=False)     

    
    print ("*******************")
    print ("clean data:")
    print ("*******************")
    print (df)
    print ("*******************")
    print ("pruned data:")
    print ("*******************")
    print (prunedDF)

testit()