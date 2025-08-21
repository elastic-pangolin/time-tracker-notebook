import os
import re
import pandas as pd
from loguru import logger
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as matcolors

# Definitions: column names in time-tracker csv file
field_name_project = "Project"
field_name_start = "Start Time"
field_name_end = "End Time"
field_name_duration_readable = "%dr"
field_name_duration_seconds = "%ds"
field_name_description = "Description"

pd.set_option('display.max_rows', None)

def prep_data(df):
    raw_df = df.copy()
    raw_df = raw_df[raw_df[field_name_start] != "deleted"]
    raw_df = raw_df.dropna(subset=[field_name_start, field_name_end])
    raw_df[field_name_start] = raw_df[field_name_start].str.replace(r' GMT.*', '', regex=True)
    raw_df[field_name_end] = raw_df[field_name_end].str.replace(r' GMT.*', '', regex=True)
    raw_df['start'] = pd.to_datetime(raw_df[field_name_start]) #, format='%a %b %d %Y %H:%M:%S')
    raw_df['end'] = pd.to_datetime(raw_df[field_name_end]) #,format='%a %b %d %Y %H:%M:%S')
    raw_df['day'] = raw_df['start'].dt.strftime('%b %d')
    
    return raw_df

# TODO: why is 2025 hardcoded?
def time_mask(full_df, BEFORE:str = None, AFTER:str = None):
    df = full_df.copy()
    if BEFORE:
        before = pd.to_datetime(BEFORE)
        print(f"Filtered only days before (incl.) {before}")
        df = df[ pd.to_datetime(df["day"] + " 2025") <= before ]
    if AFTER:
        after = pd.to_datetime(AFTER)
        print(f"Filtered only days after (incl.) {after}")
        df = df[ pd.to_datetime(df["day"] + " 2025") >= after ]
    return df

def calc_alltime_totals(df):
    eval_total = {}
    eval_days = {}
    covered_days = df['day'].unique()
    covered_projects = df[field_name_project].unique()
    for day in covered_days:
        day_df = df[df['day'] == day]
        eval_day = {}
        total_tracked_day = 0
        
        for project in covered_projects:
            if not eval_total.get(project):
                eval_total[project] = 0
            eval_day[project] = day_df[day_df[field_name_project] == project][field_name_duration_seconds].sum()
            if project != 'TOTALS':
                total_tracked_day += eval_day[project]
            eval_total[project] += eval_day[project]

        #print(eval_day['TOTALS'], " - ", total_tracked_day)
        eval_day['untracked'] = eval_day['TOTALS'] - total_tracked_day
        eval_days[day] = eval_day
        
        if not eval_total.get('untracked'):
            eval_total['untracked'] = 0
        eval_total['untracked'] += eval_day['untracked']
    return eval_total

def add_daily_totals(og_df):
    df = og_df.copy()
    # calculate totals
    covered_days = df['day'].unique()
    for day in covered_days:
        day_df = df[df['day'] == day]
        work_start = day_df['start'].min()
        work_end = day_df['end'].max()
        diff = work_end - work_start
        day_total_row = pd.DataFrame({'start': [work_start], 'end': [work_end], field_name_project: 'TOTALS', 'day': day, 
                                  field_name_duration_seconds: diff.total_seconds(), 
                                  field_name_duration_readable: str(diff) })
        df = pd.concat([day_total_row, df], ignore_index=True)
    return df

def ticket_summary(df):
    result = []
    covered_days = df['day'].unique()
    for day in covered_days:
        ticket_df = df[(df[field_name_project] != "work") & (df[field_name_project] != "TOTALS") & (df[field_name_project] != "LUNCH") & (df[field_name_project] != "BREAKS")]
        ticket_df = ticket_df[ticket_df["day"] == day]

        ticketkey_pattern = r'[A-Z]+-[0-9]+'
        ticket_agg = {}
        ticket_agg["OTHER"] = ( df[(df[field_name_project] == "TOTALS") & (df["day"] == day)][field_name_duration_seconds].sum() 
                       - df[(df[field_name_project] == "LUNCH") & (df["day"] == day)][field_name_duration_seconds].sum())

        #print (f"overall worked on {day}: {ticket_agg['OTHER']/60} min")

        for project in ticket_df[field_name_project].unique(): 
            match = re.search(ticketkey_pattern, project)
            keyname = None
            if match:
                keyname = match.group()
            if keyname:
                if not ticket_agg.get(keyname):
                    ticket_agg[keyname] = 0
                ticket_time = ticket_df[ticket_df[field_name_project] == project][field_name_duration_seconds].sum()
                ticket_agg[keyname] += ticket_time
                ticket_agg["OTHER"] -= ticket_time

        for desc in ticket_df['Description'].unique():
            if not isinstance(desc, str):
                continue
            match = re.search(ticketkey_pattern, desc)
            keyname = None
            if match:
                keyname = match.group()
            if keyname:
                if not ticket_agg.get(keyname):
                    ticket_agg[keyname] = 0
                ticket_time = ticket_df[ticket_df[field_name_description] == desc][field_name_duration_seconds].sum()
                ticket_agg[keyname] += ticket_time
                ticket_agg["OTHER"] -= ticket_time

        ticket_agg = {key:(value/60) for key, value in ticket_agg.items()}

        result.append( (day, ticket_agg) )
    return result