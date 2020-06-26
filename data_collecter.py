# -*- coding: utf-8 -*-
"""
Created on Thu Jun 25 21:06:38 2020

@author: Mark JP Sanchez
"""

import json
import requests
import pandas as pd

#Sets up variables for data collection from api
api_key = "PUT-API-KEY"
api_url = "https://www.thebluealliance.com/api/v3"

headers = {
    'Content-Type': 'application/json',
    'X-TBA-Auth-Key': api_key
}

#Collecting TEAM data

#Rows list is used to store all the data before its turned into a dataframe
rows_list = []

#Gets team response from api
response = requests.get(api_url + '/teams/0', headers=headers)
raw_data = response.json()

index = 0
#Ensures the collection stops when there is no more teams left to gather
while len(raw_data) > 0:
    print("On page " + str(index) + "...")
    
    for team in raw_data:
        row = {}
        
        for key, value in team.items():
            row[key] = value
            
        rows_list.append(row)
        
    #Iterates through the team list
    index += 1
    response = requests.get(api_url + '/teams/' + str(index), headers=headers)
    raw_data = response.json()
    
#Turns row list into a dataframe
team_df = pd.DataFrame(rows_list)

#Saves teams dataframe to csv file
team_df.to_csv('raw_frc_teams.csv')