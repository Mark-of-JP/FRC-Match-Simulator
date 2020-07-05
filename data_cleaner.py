# -*- coding: utf-8 -*-
"""
Created on Fri Jun 26 11:20:48 2020

@author: Mark JP Sanchez
"""

#%%
import pandas as pd

#%%

#Get the three dataframs
team_df = pd.read_csv('raw_frc_teams.csv')
match_df = pd.read_csv('raw_frc_matches.csv')
awards_df = pd.read_csv('raw_frc_awards.csv')

#%%

#Removal of rows and columns

#Remove unwanted columns
match_df = match_df.drop(columns=['Unnamed: 0', 'actual_time', 'predicted_time'])

#Remove rows that have matches that don't contain 3 teams per alliance
for i in range(3):
    match_df = match_df[match_df['red_' + str(i)].notna()]
    match_df = match_df[match_df['blue_' + str(i)].notna()]
    
#Remove rows that have no time or negative time
match_df = match_df[match_df['time'].notna()]
match_df = match_df.drop(match_df[match_df.time < 0].index)

#Remove rows that have no winners
match_df = match_df[match_df['winning_alliance'].notna()]

#Remove teams that are not found in team df
frc_team_keys = []
for index, row in team_df.iterrows():
    frc_team_keys.append(row['key'])
    
for i in range(3):
    match_df = match_df[match_df['red_' + str(i)].isin(frc_team_keys)]
    match_df = match_df[match_df['blue_' + str(i)].isin(frc_team_keys)]

#Change unix time to datetime
match_df['time'] = pd.to_datetime(match_df['time'], unit='s')
match_df.sort_values(by='time', inplace=True)

#Reset the index
match_df = match_df.reset_index(drop=True)

#Get earliest years for awards and matches
earliest_award_year, earliest_match_year = 1992, 2016

#Add a year column since every year is a new game
match_df['year'] = match_df['time'].apply(lambda x : x.year)
#Data before 2014 is scarce
match_df = match_df[match_df['year'] >= earliest_match_year]

#%%

#Format proper data and extract new data 

#Change winning alliance to red win
match_df['red_won'] = 0
match_df.loc[match_df['winning_alliance'] == 'red', 'red_won'] = 1

#Get Average Data
team_data = {}

#Adds a team to team data and initializes its default values
def initialize_team(team_key):
    team_data[team_key] = {}
    
    #Initialize awards
    team_data[team_key]['match_awards'] = 0
    team_data[team_key]['other_awards'] = 0
    
    #Initialize games
    team_data[team_key]['games_played'] = 0
    team_data[team_key]['games_won'] = 0
    
    team_data[team_key]['games_played_season'] = 0
    team_data[team_key]['games_won_season'] = 0
    team_data[team_key]['points_season'] = 0
    
    team_data[team_key]['elo'] = 1500
    
    team_data[team_key]['rookie_year'] = team_df[team_df['key'] == team_key]['rookie_year'].item()
    
#Adds awards to team from a certain event
def add_event_awards(event_key):
    if event_key is None:
        return
    
    event_awards_df = awards_df[awards_df['event_key'] == event_key]
    
    for index, row in event_awards_df.iterrows():
        team_key = row['recipient']
        
        if team_key not in team_data:
            initialize_team(team_key)
            
        if row['award_type'] in match_award_types:
            team_data[team_key]['match_awards'] += 1
        else:
            team_data[team_key]['other_awards'] += 1
        

#Get initial award data
#Splitting the awards into match awards and other awards
#Award types can be found here: https://github.com/the-blue-alliance/the-blue-alliance/blob/master/consts/award_type.py#L15
match_award_types = [0, 1, 2, 10, 14]
    
print('Initializing initial awards...')
for year in range(earliest_award_year, earliest_match_year):
    print('Formatting awards for the year ' + str(year))
    year_award_df = awards_df[awards_df['year'] == year]
    
    for index, row in year_award_df.iterrows():
        team_key = row['recipient']
        
        if team_key not in team_data:
            initialize_team(team_key)
            
        if row['award_type'] in match_award_types:
            team_data[team_key]['match_awards'] += 1
        else:
            team_data[team_key]['other_awards'] += 1
            
#Stores number of matches for giving awards from events
print("Recording number of matches per event")
num_of_matches_per_event = {}
event_groupby = match_df.groupby('event_key')
for event_key, group in event_groupby:
    num_of_matches_per_event[event_key] = len(match_df[match_df.event_key == event_key])
            
#Adding team data to matches dataframe
print('Adding team data to matches...')
match_df['red_avg_match_awards'] = 0
match_df['red_avg_other_awards'] = 0

match_df['blue_avg_match_awards'] = 0
match_df['blue_avg_other_awards'] = 0

match_df['red_avg_winrate'] = 0
match_df['red_avg_games_played'] = 0

match_df['blue_avg_winrate'] = 0
match_df['blue_avg_games_played'] = 0

match_df['red_avg_age'] = 0
match_df['blue_avg_age'] = 0

match_df['red_points_ratio_season'] = 0
match_df['red_avg_winrate_season'] = 0
match_df['red_avg_games_played_season'] = 0
match_df['blue_avg_winrate_season'] = 0
match_df['blue_avg_games_played_season'] = 0

match_df['red_elo'] = 0
match_df['blue_elo'] = 0
match_df['elo_prediction'] = 0

#Functions for formatting data
def get_avg_awards(alliance):
    total_match_awards = 0.0
    total_other_awards = 0.0
    
    for team_key in alliance:
        total_match_awards += team_data[team_key]['match_awards']
        total_other_awards += team_data[team_key]['other_awards']
        
    return total_match_awards / len(alliance), total_other_awards / len(alliance)

def get_avg_games(alliance, boundary=''):
    total_games_played = 0
    total_wins = 0
    
    for team_key in alliance:
        total_games_played += team_data[team_key]['games_played' + boundary]
        total_wins += team_data[team_key]['games_won' + boundary]
        
    winrate = 0.5 if total_games_played == 0 else total_wins / total_games_played
        
    return total_games_played / len(alliance), winrate

def get_avg_age(alliance, current_year):
    total_age = 0
    
    for team_key in alliance:
        total_age += current_year - team_data[team_key]['rookie_year']
        
    return total_age / len(alliance)

def get_red_points_ratio(red_alliance, blue_alliance, boundary='_season'):
    total_red_avgs = 0
    total_blue_avgs = 0
    
    for team_key in red_alliance:
        if team_data[team_key]['games_played' + boundary] == 0:
            return 1
        
        total_red_avgs += (team_data[team_key]['points' + boundary] / team_data[team_key]['games_played' + boundary])
            
    for team_key in blue_alliance:
        if team_data[team_key]['games_played' + boundary] == 0:
            return 1
        total_blue_avgs += (team_data[team_key]['points' + boundary] / team_data[team_key]['games_played' + boundary])
    
    if total_blue_avgs == 0 or total_red_avgs == 0:
        return 1
    
    return total_red_avgs / total_blue_avgs

def get_elo_average(alliance):
    total_elo = 0
    
    for team_key in alliance:
        total_elo += team_data[team_key]['elo']
        
    return total_elo / len(alliance)

def get_elo_prediction(red_alliance_elo, blue_alliance_elo):
    elo_delta = blue_alliance_elo - red_alliance_elo
    
    return 1 / (1 + (10**(elo_delta / 400)))

def change_elo(alliance, prediction, result):
    for team_key in alliance:
        team_data[team_key]['elo'] += 10 * (result - prediction)

def reset_season():
    
    for team_key in team_data:
        team_data[team_key]['games_played'] += team_data[team_key]['games_played_season']
        team_data[team_key]['games_won'] += team_data[team_key]['games_won_season']
        
        team_data[team_key]['games_played_season'] = 0
        team_data[team_key]['games_won_season'] = 0
        team_data[team_key]['points_season'] = 0

#Set up variables for iteration through the matches
curr_year = None
len_match = len(match_df)
match_df = match_df.reset_index(drop=True)
#Iterate/simulate each match
for index, row in match_df.iterrows():
    
    print('Engineering features for match ' + str(index) + "/" + str(len_match))
    
    if row['year'] != curr_year:
        curr_year = row['year']
        reset_season()
        
    #Get the red and blue alliance
    red_alliance = [row['red_0'], row['red_1'], row['red_2']]
    blue_alliance = [row['blue_0'], row['blue_1'], row['blue_2']]
    
    #Initialize the teams
    for i in range(3):
        if red_alliance[i] not in team_data:
            initialize_team(red_alliance[i])
        if blue_alliance[i] not in team_data:
            initialize_team(blue_alliance[i])
        
    #Add data to the datafram
    row['red_avg_match_awards'], row['red_avg_other_awards'] = get_avg_awards(red_alliance)
    row['blue_avg_match_awards'], row['blue_avg_other_awards'] = get_avg_awards(blue_alliance)
    
    row['red_avg_games_played'], row['red_avg_winrate'] = get_avg_games(red_alliance)
    row['blue_avg_games_played'], row['blue_avg_winrate'] = get_avg_games(blue_alliance)
    
    row['red_avg_games_played_season'], row['red_avg_winrate_season'] = get_avg_games(red_alliance, boundary='_season')
    row['blue_avg_games_played_season'], row['blue_avg_winrate_season'] = get_avg_games(blue_alliance, boundary='_season')

    row['red_points_ratio_season'] = get_red_points_ratio(red_alliance, blue_alliance)
    
    row['red_avg_age'] = get_avg_age(red_alliance, row['time'].year)
    row['blue_avg_age'] = get_avg_age(blue_alliance, row['time'].year)
    
    row['red_elo'] = get_elo_average(red_alliance)
    row['blue_elo'] = get_elo_average(blue_alliance)
    
    red_pred = get_elo_prediction(row['red_elo'], row['blue_elo'])
    blue_pred = get_elo_prediction(row['blue_elo'], row['red_elo'])
    
    row['elo_prediction'] = red_pred
    
    #Add match stats to the teams
    if row['red_won'] == 1:
        for team_key in red_alliance:
            team_data[team_key]['games_won_season'] += 1
            
        change_elo(red_alliance, red_pred, 1)
        change_elo(blue_alliance, blue_pred, 0)
    else:
        for team_key in blue_alliance:
            team_data[team_key]['games_won_season'] += 1
            
        change_elo(red_alliance, red_pred, 0)
        change_elo(blue_alliance, blue_pred, 1)
            
    for team_key in (blue_alliance + red_alliance):
        team_data[team_key]['games_played_season'] += 1
       
    for team_key in red_alliance:
        team_data[team_key]['points_season'] += row['red_score']
        
    for team_key in blue_alliance:
        team_data[team_key]['points_season'] += row['red_score']
        
    #Add new event awards if previous event has passed
    num_of_matches_per_event[row['event_key']] -= 1
    if num_of_matches_per_event[row['event_key']] <= 0:
        add_event_awards(row['event_key'])
        # reset_match(row['event_key'])
    
    match_df.loc[index] = row
    
#Get differences for the features that require differences
match_df['avg_match_awards_diff'] = match_df['red_avg_match_awards'] - match_df['blue_avg_match_awards']
match_df['avg_other_awards_diff'] = match_df['red_avg_other_awards'] - match_df['blue_avg_other_awards']
match_df['avg_winrate_diff'] = match_df['red_avg_winrate'] - match_df['blue_avg_winrate']
match_df['avg_games_played_diff'] = match_df['red_avg_games_played'] - match_df['blue_avg_games_played']
match_df['avg_age_diff'] = match_df['red_avg_age'] - match_df['blue_avg_age']
match_df['avg_winrate_diff_season'] = match_df['red_avg_winrate_season'] - match_df['blue_avg_winrate_season']
match_df['avg_games_played_diff_season'] = match_df['red_avg_games_played_season'] - match_df['blue_avg_games_played_season']

#%%
#Get the use case dataframe and create a csv
use_case_df = match_df
use_case_df.to_csv('frc_use_case.csv')

