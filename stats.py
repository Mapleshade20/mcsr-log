# Created by MapleShade20
# Intance folders here should be named like: Instance 4

import json
import os
import pandas as pd
import logging
import datetime

# 读取config.json
try:
  with open('./config.json', "r") as f:
    config = json.load(f)
  your_path = config['path']
  read_incomplete = config['read_incomplete']
  ignore_lastrun = config['ignore_lastrun']
  version = config['version']
except Exception:
  print('Cannot find config.json. It\'s recommended to run me under my own directory.')
  if not os.path.exists('instgroups.json'):
    your_path = str(input('Please enter MultiMC directory. Should be like D:\Program Files\MultiMC\instances (edit config.json is recommended)\nEnter: '))
  else:
    your_path = '.'
  read_incomplete = False
  version = None
os.chdir(your_path)

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', filename='stats.log', filemode='a', encoding='utf-8', level=logging.DEBUG)
logging.info(f'Running at {os.getcwd()}')
if read_incomplete:
  logging.info("Will read incomplete saves!!!")
else: 
  logging.info("Will only read completed saves.")
if not os.path.exists("stats_last_run.txt"):
  logging.info("No stats_last_run.txt")

# 定义一个函数，判断一个文件夹是否是新创建的
def is_new_folder(folder):

  # 获取文件夹的创建时间
  folder_ctime = os.path.getctime(folder)

  # 获取上次运行程序的时间，在last_run.txt文件中
  if not os.path.exists("./stats_last_run.txt"):
    return True
  else:
    with open("./stats_last_run.txt", "r") as f:
      try:
        last_run_time = float(str(f.read()))
      except Exception:
        logging.error('Unable to read stats_last_run.txt.')
        print('Please delete stats_last_run.txt and run again.')
        exit()
      logging.debug(f'Save \'{folder}\' detected. Create time: {datetime.datetime.fromtimestamp(folder_ctime)}. Last stats: {datetime.datetime.fromtimestamp(last_run_time)}.')
    # 如果文件夹的创建时间大于上次运行程序的时间，返回True，否则返回False
    return folder_ctime > last_run_time

# 定义一个函数，用来把毫秒转化为分秒的格式
def convert_millis(millis):
  # 用datetime.timedelta方法来创建一个时间差对象，用毫秒数除以1000得到秒数
  delta = datetime.timedelta(seconds = millis/1000)
  # 用str方法来把时间差对象转换为字符串，格式为'HH:MM:SS.ffffff'
  delta_str = str(delta)
  # 用split方法来把字符串按照':'分割为三部分，分别是小时，分钟，秒毫秒
  hour, minute, second = delta_str.split(':')
  second = second[:6]
  # 用format方法来把分钟，秒和毫秒拼接成你想要的格式，即'分:秒.毫秒'
  result = f'{hour}:{minute}:{second}'
  # 返回一个字符串，格式为"分:秒"
  return result

# 定义一个函数，用来计算一个片段的时间
# THIS FUNCTION SHALL BE MODIFIED IN FUTURE VERSIONS
def length(total: int, stamp2: str, dataframe: pd.DataFrame, rename2: str):
  stamp_seconds = int(dataframe[stamp2].igt / 1000)
  # fortress first?
  if total == -1:
    print('In one save you entered fortress before bastion, so your fight_blaze time cannot be calculated. It\'s marked as -1.')
    length = -1
  elif stamp_seconds < total:
    try: # some very weird enter order (SSG maybe) may lead to error
      length = stamp_seconds - total + dataframe['goto_bastion'] # fort - neth = fort - bas + (bas - neth)
      dataframe['goto_bastion'] = total - stamp_seconds
      stamp_seconds = -1
    except KeyError:
      length = -1
  else:
    length = stamp_seconds - total
  dataframe = dataframe.drop(columns=stamp2)
  dataframe[rename2] = length
  return dataframe, stamp_seconds


# ------
# VERSION CHECK
# ------

if os.path.exists('stats_output.csv'):
  version_check = pd.read_csv('stats_output.csv')
  try:
    values = version_check.loc[:, 'goto_bastion']
  except Exception:
    print('Your CSV is in an older version. Please delete it along with \'stats_last_run.txt\' and run again.')
    exit()
print(f'Your script version is {version}')


# ------
# READ
# ------

data = None
splits_match = {'enter_nether':'enter_nether', 'enter_bastion':'goto_bastion',
               'enter_fortress':'bart_n_goto_fort', 'nether_travel':'fight_blaze',
               'enter_stronghold':'eye_spy', 'enter_end':'locate_room',
               'kill_ender_dragon':'kill_dragon'}

for instance in os.listdir("."):
  # 只打开Instance *
  if not instance.startswith('Instance'):
    continue
  logging.info(f'Current folder: {instance}')

  # 遍历当前目录下的所有文件夹
  for save in os.listdir(f"./{instance}/.minecraft/saves"):
    save_path = f"/{instance}/.../{save}"
    logging.debug(f"Start checking /{instance}/.minecraft/saves/{save}")
    if not save.startswith("Random Speedrun") and not save.startswith("Set Speedrun"):
      continue

    # 判断是否是新创建的save，如果不是，检查下一个save
    if not ignore_lastrun:
      if not is_new_folder(f"./{instance}/.minecraft/saves/{save}"):
        continue

    # 拼接文件夹名和record.json的路径
    record_path = os.path.join(f"./{instance}/.minecraft/saves", save, "speedrunigt/record.json")

    # 判断record.json文件是否存在，如果不是，检查下一个save
    if not os.path.exists(record_path):
      logging.warning(f'Cannot find record in \'{record_path}\'.')
      continue
    
    # 打开record.json文件
    with open(record_path, "r") as f:
      # 读取文件内容并转换为字典
      record = json.load(f)
    
    splits = ['enter_nether', 'enter_bastion', 'enter_fortress',
            'nether_travel', 'enter_stronghold', 'enter_end', 'kill_ender_dragon']
    
    # 判断is_completed是否为true
    if record["is_completed"]:

      logging.info(f"/{instance}/.../{save} matches!")
      df = pd.DataFrame(record["timelines"]).set_index("name").T
      df = df.drop(index='rta')
      # logging.debug(df)

      temp = 0
      for split in splits:
        df, temp = length(temp, split, df, splits_match[split])

      # date和igt转换。date除以1000，因为Python的时间戳是以秒为单位的
      # date是以毫秒为单位的时间戳，表示从1970年1月1日0时0分0秒（UTC）开始到某个时间点的毫秒数
      date_converted = datetime.datetime.fromtimestamp(record["date"] / 1000).strftime("%Y-%m-%d %H:%M")
      final_igt_converted = convert_millis(record["final_igt"])

      # 把值添加到数据框对象中，作为新的列
      df["category"] = record["category"]
      df["run_type"] = record["run_type"]
      df["final_igt"] = record["final_igt"]
      df["final_rta"] = record["final_rta"]
      df["date"] = record["date"]
      df["date_converted"] = date_converted
      df["final_igt_converted"] = final_igt_converted
      df["save_path"] = save_path
      df["is_completed"] = record["is_completed"]

      # 整理列
      #   如果不在，用pandas.DataFrame.assign方法来添加一列'portal_no_2'，并把值设定为'N/A'
      #   df = df.assign(portal_no_2=-1)
      # 
      df = df[['category','run_type','is_completed','final_igt_converted','date_converted','enter_nether',
              'goto_bastion','bart_n_goto_fort','fight_blaze','eye_spy','locate_room','kill_dragon',
              'save_path','date','final_igt','final_rta']]
    
    elif read_incomplete:
      if record["timelines"] == []:
        logging.debug(f"[INCOMPLETE] /{instance}/.../{save} skipped! No timelines.")
        continue
      df = pd.DataFrame(record["timelines"]).set_index("name").T
      df = df.drop(index='rta')
      if 'enter_stronghold' in df.columns:  # incomplete TARGET
        logging.info(f"[INCOMPLETE] /{instance}/.../{save} matches!")
        timelines_incomp = []
        timelines_incomp.extend(list(df.columns))
        #print(timelines_incomp)
        temp = 0
        splits_dup = splits[:]
        #print('1\n', splits)
        for split in splits:
          if split in timelines_incomp:
            df, temp = length(temp, split, df, splits_match[split])
            #print(split, 'is in! \n', df)
          else:
            #print(split, 'isnt in! \n', df)
            break
          splits_dup.remove(split)
        for remained in splits_dup:
          df[splits_match[remained]] = -1
          #print('2', split, '\n', df)
        #print('\n\n\n')
        date_converted = datetime.datetime.fromtimestamp(record["date"] / 1000).strftime("%Y-%m-%d %H:%M")
        # 把值添加到数据框对象中，作为新的列
        df["category"] = record["category"]
        df["run_type"] = record["run_type"]
        df["final_igt"] = -1
        df["final_rta"] = -1
        df["date"] = record["date"]
        df["date_converted"] = date_converted
        df["final_igt_converted"] = -1
        df["save_path"] = save_path
        df["is_completed"] = record["is_completed"]

        df = df[['category','run_type','is_completed','final_igt_converted','date_converted','enter_nether',
              'goto_bastion','bart_n_goto_fort','fight_blaze','eye_spy','locate_room','kill_dragon',
              'save_path','date','final_igt','final_rta']]

      else:
        logging.debug(f"[INCOMPLETE] /{instance}/.../{save} skipped! No \'nether_travel\'.")
        continue

    else:
      logging.debug(f"Skipping \'{save}\' for it is not completed.")
      continue
      

    if data is not None:
      data = pd.concat([data, df], axis=0, ignore_index=True)
    else:
      data = df

# 把数据框对象保存为stats_output.csv文件
if data is None:
  print('No new runs detected.')
elif not os.path.exists('stats_output.csv'):
  data.sort_values(by='date')
  logging.info('Initiating stats_output.csv')
  data.to_csv("stats_output.csv", index=False, header=True)
else:
  data.sort_values(by='date')
  logging.info('Writing into stats_output.csv')
  data.to_csv("stats_output.csv", mode='a', index=False, header=False)


# ----------
# TIME WRITE
# ----------
# 获取当前时间
current_time = datetime.datetime.now().timestamp()
with open("stats_last_run.txt", "w") as f:
  # 写入文件
  f.write(str(float(current_time)))
  logging.debug(f"Execute time: {datetime.datetime.now()}, {current_time}")

print("Completed.")
