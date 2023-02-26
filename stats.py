# Created by MapleShade20
# Intance folders here should be named like: Instance 4

import json
import os
import pandas as pd
import logging
import datetime

your_path = 'D:\Program Files\MultiMC\instances'
read_incomplete = True

if not os.path.exists('instgroups.json'):
  if not os.path.exists(your_path):
    your_path = str(input('Please enter MultiMC directory, which should be like D:\Program Files\MultiMC\instances. (You may also edit stats.py line 10)\nEnter: '))
    os.chdir(your_path)
  else:
    os.chdir(your_path)

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', filename='stats.log', filemode='a', encoding='utf-8', level=logging.DEBUG)

logging.info(f'Running at {os.getcwd()}')

if not os.path.exists("stats_last_run.txt"):
  logging.info("First time running this script.")

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
# THIS FUNCTION SHALL BE REDEFINED IN FUTURE VERSIONS
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
  dataframe.drop(stamp2, axis=1)
  dataframe[rename2] = length
  return dataframe, stamp_seconds


# ------
# VERSION FATAL
# ------

if os.path.exists('stats_output.csv'):
  version_check = pd.read_csv('stats_output.csv')
  try:
    values = version_check.loc[:, 'goto_bastion']
  except Exception:
    print('Your CSV is in older version. Please delete it along with \'stats_last_run.txt\' and run again.')
    exit()

# ------
# READ
# ------

data = None

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
    check_new = is_new_folder(f"./{instance}/.minecraft/saves/{save}")
    if not check_new:
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
    
    # 判断is_completed是否为true，如果不是，检查下一个save
    if not record["is_completed"]:
      logging.debug(f"Record \'{save}\' is not completed.")
      continue

    logging.info(f"/{instance}/.minecraft/saves/{save} matches!")
    df = pd.DataFrame(record["timelines"]).set_index("name").T
    df = df.drop(index='rta')
    # logging.debug(df)

    df, temp = length(0, 'enter_nether', df, 'enter_nether')
    df, temp = length(temp, 'enter_bastion', df, 'goto_bastion')
    df, temp = length(temp, 'enter_fortress', df, 'goto_fortress')
    df, temp = length(temp, 'nether_travel', df, 'fight_blaze')
    df, temp = length(temp, 'enter_stronghold', df, 'eye_spy')
    df, temp = length(temp, 'enter_end', df, 'locate_room')
    df, temp = length(temp, 'kill_ender_dragon', df, 'kill_dragon')

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

    # 整理列
    #   如果不在，用pandas.DataFrame.assign方法来添加一列'portal_no_2'，并把值设定为'N/A'
    #   df = df.assign(portal_no_2=-1)
    # 
    df = df[['category','run_type','final_igt_converted','date_converted','date','final_igt','final_rta','enter_nether',
             'goto_bastion','goto_fortress','fight_blaze','eye_spy','locate_room','kill_dragon','save_path']]
    
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
