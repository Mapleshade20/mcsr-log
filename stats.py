# Created by MapleShade20
# Intance folders here should be named like: Instance 4

import json
import os
import pandas as pd
import logging
import datetime

your_path = 'D:\Program Files\MultiMC\instances'
if not os.path.exists('instgroups.json'):
  if not os.path.exists(your_path):
    your_path = str(input('Please enter your MultiMC directory. It should be like: D:\Program Files\MultiMC\instances'))
    os.chdir(your_path)
  else:
    os.chdir(your_path)

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', filename='stats.log', filemode='a', encoding='utf-8', level=logging.DEBUG)

logging.info(f'Running at {os.getcwd()}')

if not os.path.exists("./stats_last_run.txt"):
  logging.info("First run.")
# 定义一个函数，判断一个文件夹是否是新创建的
def is_new_folder(folder):

  # 获取文件夹的创建时间
  folder_ctime = os.path.getctime(folder)

  # 获取上次运行程序的时间，在last_run.txt文件中
  if not os.path.exists("./stats_last_run.txt"):
    return True
  else:
    with open("./stats_last_run.txt", "r") as f:
      last_run_time = float(str(f.read()))
      logging.debug(f'Save \'{folder}\' detected. Create time: {folder_ctime}. Last stats: {last_run_time}.')
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
  result = f'{minute}:{second}'
  # 返回一个字符串，格式为"分:秒"
  return result

for instance in os.listdir("."):
  # 只打开Instance *
  if not instance.startswith('Instance'):
    continue
  logging.info(f'Current folder: {instance}')

  # 遍历当前目录下的所有文件夹
  for save in os.listdir(f"./{instance}/.minecraft/saves"):
    logging.debug(f"Start checking /{instance}/.minecraft/saves/{save}")
    if not save.startswith("Random Speedrun"):
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

    # # 判断是否有portal_no_2，如没有则补足
    # columns = df.columns
    # # 用'in'运算符来判断'portal_no_2'是否在列名列表中
    # if 'portal_no_2' not in columns:
    #   # 如果不在，用pandas.DataFrame.assign方法来添加一列'portal_no_2'，并把值设定为'N/A'
    #   df = df.assign(portal_no_2=-1)
    df = df[['category','run_type','final_igt_converted','date_converted','date','final_igt','final_rta','enter_nether',
             'enter_bastion','enter_fortress','nether_travel','enter_stronghold','enter_end','kill_ender_dragon']]

    # 把数据框对象保存为stats_output.csv文件
    if not os.path.exists('stats_output.csv'):
      logging.info('Initiating stats_output.csv')
      df.to_csv("stats_output.csv", index=False, header=True)
    else:
      logging.info('Writing into stats_output.csv')
      df.to_csv("stats_output.csv", mode='a', index=False, header=False)

try:
  current_time = os.path.getmtime("stats_output.csv")
  with open("stats_last_run.txt", "w") as f:
  # 获取当前时间
    current_time = os.path.getmtime("stats_output.csv")
    # 写入文件
    f.write(float(current_time))
    logging.debug("Recorded running time.")
except Exception:
  logging.error('No csv already exists.')
  with open("stats_last_run.txt", "w") as f:
  # 获取当前时间
    current_time = os.path.getmtime("stats_output.csv")
    # 写入文件
    f.write(str(float(current_time)))
    logging.debug("Recorded running time.")

logging.info('Run completed.')
print("Completed.")