# Created by MapleShade20
# Intance folders here should be named like: Instance 4

import json
import os
import pandas as pd
import logging
import datetime
import shutil

name_match = {'enter_nether':'enter_nether', 'enter_bastion':'goto_bastion',
                            'enter_fortress':'bart_travel', 'nether_travel':'fight_blaze',
                            'enter_stronghold':'eye_spy', 'enter_end':'locate_room',
                            'kill_ender_dragon':'kill_dragon'}
old_names = list(name_match.keys())
new_names = list(name_match.values())

# Fetch config.json file
try:
    with open('./config.json', "r") as f:
        config = json.load(f)
    py_dir = os.getcwd()
    mc_dir = config['mc_dir']
    read_incomplete = config['read_incomplete']
    #ignore_lastrun = config['ignore_lastrun']
    ignore_lastrun = True
    log_level = config['log_level']
    version = config['version']
    empty_bopping = config['empty_bopping']
    no_blind_bopping = config['no_blind_bopping']
    replace_old_csv = config['replace_old_csv']
except Exception:
    print('Cannot find config.json. Exiting...')
    exit()

# Check ./output/stats_output.csv version by verifying if the columns are latest.
# If not, ask user to delete the old csv, and then exit.
if os.path.exists('./output/stats_output.csv'):
    with open('./output/stats_output.csv', 'r') as f:
        if f.readline().strip() != 'category,run_type,is_completed,final_igt_converted,date_converted,' + ','.join(new_names) + ',save_path,date,final_igt,final_rta':
            print('You have an outdated stats_output.csv. Please delete it. Exiting...')
            exit()
else:
    pass

# Set up logging
os.chdir(py_dir)
logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', filename='stats.log', filemode='a', encoding='utf-8', level=log_level)
logging.info(f'Running at {os.getcwd()}')

# Log config used
logging.info(f'Config used: {config}')

# Check if stats_last_run.txt exists, and define last_run_time
if os.path.exists("stats_last_run.txt"):
    with open("./stats_last_run.txt", "r") as f:
        try:
            last_run_time = float(str(f.read()))
        except Exception:
            logging.error('stats_last_run.txt is broken.')
            print('Please delete stats_last_run.txt. Exiting...')
            exit()
else:
    logging.info("Cannot find stats_last_run.txt")
    last_run_time = 0

# Change working directory to MultiMC
os.chdir(mc_dir)

# Check if path is valid, by verifying if mc_dir is a string ending with 'instances'
if not mc_dir.endswith('instances'):
    print(f'Invalid path: {mc_dir}. Exiting...')
    exit()

# Define a function to check if a folder is new
def is_new_folder(folder, last_run_time):

    # Get folder create time
    folder_ctime = os.path.getctime(folder)
    
    if last_run_time != 0:
        logging.debug(f'Save \'{folder}\' created at: {datetime.datetime.fromtimestamp(folder_ctime)}. Last stats: {datetime.datetime.fromtimestamp(last_run_time)}.')
        # If folder create time is later than last run time, return True
        return folder_ctime > last_run_time
    else:
        return True

# Define a function to convert milliseconds to minutes and seconds
def convert_millis(millis):
    delta = datetime.timedelta(seconds = millis/1000) # in seconds
    # Get string 'HH:MM:SS.ffffff'
    delta_str = str(delta)
    # Split to get 'HH:MM:SS.fff'
    hour, minute, second = delta_str.split(':')
    second = second[:6]
    result = f'{hour}:{minute}:{second}'
    return result

# Main record reader module
def read_record(record, old_names, new_names):
    # 'record': json.load() object, 'old_names': list, 'new_names': list
    # Import record timelines
    df = pd.DataFrame(record["timelines"]).set_index("name").T
    df = df.drop(index='rta')
    if not ('enter_fortress' in df.columns and 'enter_bastion' in df.columns and 'nether_travel' in df.columns):
        # logging.debug(f'In {save}, you didn\'t complete bastion & fortress. Skipped.')
        return None
    
    # Calculate time
    base = pd.DataFrame()
    for i in range(len(old_names)):
        # check if df[old_names[i]] exists
        if old_names[i] not in df.columns:
            # set all remaining columns to -1
            for j in range(i, len(old_names)):
                base[new_names[j]] = -1
            break
        if i == 0:
            base[new_names[i]] = df[old_names[i]] / 1000     # enter_nether
        elif df[old_names[i]].item() < df[old_names[i-1]].item():
            # i: enter_fortress, i-1: enter_bastion
            # original: bart_travel = enter_fortress - enter_bastion < 0
            # new: bart_travel = nether_travel - enter_bastion > 0
            base[new_names[i]] = (df[old_names[i+1]] - df[old_names[i-1]]) / 1000
            # original: goto_bastion = enter_bastion - enter_nether
            # new: goto_bastion = enter_bastion - enter_fortress
            base[new_names[i-1]] = (df[old_names[i-1]] - df[old_names[i]]) / 1000
            # unchanged: fight_blaze = nether_travel - enter_fortress
        else:
            base[new_names[i]] = (df[old_names[i]] - df[old_names[i-1]]) / 1000
    return base.astype(int)

# ------
# READ
# ------

count = 0
data = None

for instance in os.listdir("."):
    # Accept 'Instance *'
    if not instance.startswith('Instance'):
        continue
    logging.info(f'Current folder: {instance}')

    for save in os.listdir(f"./{instance}/.minecraft/saves"):
        path_info = f"/{instance}/{save}"
        if not save.startswith("Random Speedrun") and not save.startswith("Set Speedrun"):
            continue
        #logging.debug(f"Start checking {path_info}")
        record_path = os.path.join(f"./{instance}/.minecraft/saves", save, "speedrunigt/record.json")
        save_path = os.path.join(f"./{instance}/.minecraft/saves", save)

        # Skip if record.json doesn't exist
        if not os.path.exists(record_path):
            logging.warning(f'Cannot find record in \'{record_path}\'.')
            continue
        
        with open(record_path, "r") as f:
            record = json.load(f)
        
        # Skip empty saves, and do world bopping if enabled
        if record["timelines"] == []:
            if empty_bopping:
                shutil.rmtree(save_path)
                logging.debug(f"Deleted empty save {path_info}.")
            continue

        # Skip old saves
        if not ignore_lastrun:
            if not is_new_folder(save_path, last_run_time):
                continue
        
        # Main read record module
        logging.info(f"{path_info} matches!")
        df = read_record(record, old_names, new_names)
        if df is None:
            if read_incomplete:
                logging.debug(f"[INC] {path_info} skipped for no \'nether_travel\'.")
            if no_blind_bopping:
                shutil.rmtree(save_path)
                logging.info(f"Deleted incomplete save {path_info}.")
            continue
        
        # date and igt conversion. date is divided by 1000 because the Python timestamp is in seconds
        # date is a millisecond timestamp that represents the number of milliseconds from 1970-1-1 0:0:0 (UTC) to a certain time point
        date_converted = datetime.datetime.fromtimestamp(record["date"] / 1000).strftime("%Y-%m-%d %H:%M")
        final_igt_converted = convert_millis(record["final_igt"])

        # Add columns
        df["category"] = record["category"]
        df["run_type"] = record["run_type"]
        df["final_igt"] = record["final_igt"]
        df["final_rta"] = record["final_rta"]
        df["date"] = record["date"]
        df["date_converted"] = date_converted
        df["final_igt_converted"] = final_igt_converted
        df["save_path"] = path_info
        df["is_completed"] = record["is_completed"]

        # Reorder columns
        df = df[['category','run_type','is_completed','final_igt_converted',
                'date_converted',*new_names,
                'save_path','date','final_igt','final_rta']]
        count += 1
        logging.info(f"Record {path_info} successfully.")

        if data is not None:
            data = pd.concat([data, df], axis=0, ignore_index=True)
        else:
            data = df

# Make a subfolder of py_dir named 'output'
os.chdir(py_dir)
if not os.path.exists('output'):
    os.makedirs('output')
os.chdir('output')

# Save the data frame object to stats_output.csv file
if data is None:
    print('No new runs detected.')
else:
    if not os.path.exists('stats_output.csv'):
        logging.info('Initiating stats_output.csv')
    elif replace_old_csv:
        logging.info('Replacing stats_output.csv')
    else:
        logging.info('Writing into stats_output.csv')
        data.to_csv("stats_output.csv", mode='a', index=False, header=False)
        data = pd.read_csv("stats_output.csv")
    # Sort the csv file by date acsendingly and then remove identical rows
    logging.info('Sorting stats_output.csv')
    data = data.sort_values(by='date', ascending=True)
    data = data.drop_duplicates(subset=['save_path'], keep='last')
    data.to_csv("stats_output.csv", mode='w', index=False, header=True)

# ----------
# TIME WRITE
# ----------
os.chdir(py_dir)
current_time = datetime.datetime.now().timestamp()
with open("stats_last_run.txt", "w") as f:
    f.write(str(float(current_time)))
    logging.info(f"Execute time: {datetime.datetime.now()}, {current_time}")

print(f"Congrats! {count} runs are recorded.")
