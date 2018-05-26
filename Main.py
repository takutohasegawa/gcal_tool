#! env python
# -*- coding: utf-8 -*-

import os
import configparser
from logging import getLogger, StreamHandler, DEBUG, FileHandler, Formatter
import datetime as dt

from module import GetGcalInfo as ggi
from module import ProcessGcalData as pgd
from module.Tools import Tools as tl

# gcal_manager.Main
# Date: 2018/04/14
# Filename: main 

__author__ = 'takutohasegawa'
__date__ = "2018/04/14"

logger = getLogger('')
fileHandler = FileHandler(__file__.replace('py', 'log'))
fileHandler.setLevel(DEBUG)
formatter = Formatter('%(asctime)s - %(levelname)s - %(message)s')
fileHandler.setFormatter(formatter)
streamHandler = StreamHandler()
streamHandler.setLevel(DEBUG)
streamHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
logger.addHandler(streamHandler)
logger.setLevel(DEBUG)

config = configparser.ConfigParser()
config.read_file(open('./config.conf', 'r', encoding='UTF-8'))

GetGcalInfo = ggi.GetGcalInfo(config)


def output(time_min, time_max, week):
    # Google Calendar情報の取得
    work_plan_info, latest_update_wp = GetGcalInfo.get_gcal_info(config['RETRIEVE']['WORK_PLAN_CAL_ID'],
                                               time_min=time_min, time_max=time_max)
    work_result_info, latest_update_wr = GetGcalInfo.get_gcal_info(config['RETRIEVE']['WORK_RESULT_CAL_ID'],
                                                 time_min=time_min, time_max=time_max)
    # life_plan_info = GetGcalInfo.get_gcal_info(config['RETRIEVE']['LIFE_PLAN_CAL_ID'])
    life_result_info, latest_update_lr = GetGcalInfo.get_gcal_info(config['RETRIEVE']['LIFE_RESULT_CAL_ID'],
                                                 time_min=time_min, time_max=time_max)

    evaluation_info, latest_update_e = GetGcalInfo.get_gcal_info(config['RETRIEVE']['EVALUATION_CAL_ID'],
                                                time_min=time_min, time_max=time_max,
                                                evaluation=True)

    latest_update = max(latest_update_wp, latest_update_wr, latest_update_lr, latest_update_e)

    last_update_path = config['GENERAL']['LAST_UPDATE_PATH']
    if os.path.exists(last_update_path):
        last_update = dt.datetime.strptime(open(last_update_path).read(), '%Y%m%d%H%M%S')
    else:
        last_update = dt.datetime(1990, 1, 1, 0, 0, 0)

    if latest_update > last_update:
        # 各カテゴリに対する時間投入量の集計し、csvファイルを出力（Life）
        ProcessGcalData = pgd.ProcessGcalData(config, week)
        ProcessGcalData.output_work_life_result(work_result_info=work_result_info, life_result_info=life_result_info,
                                                time_min=time_min, time_max=time_max)

        ProcessGcalData.output_work_plan_result(work_plan_info=work_plan_info, work_result_info=work_result_info,
                                                time_min=time_min, time_max=time_max)

        ProcessGcalData.output_life_timeline(work_result_info=work_result_info, life_result_info=life_result_info,
                                             evaluation_info=evaluation_info,
                                             time_min=time_min, time_max=time_max)

        open(last_update_path, 'w').write(latest_update.strftime('%Y%m%d%H%M%S'))

    else:
        logger.debug('No update detected.')

# 出力する週リストの取得
now = dt.datetime.now()
this_week = tl.get_week(now)

existing_files = os.listdir(config['GENERAL']['UPLOAD_DIR'])
existing_weeks = set([filename.replace('.html', '')[-8:] for filename in existing_files if '.html' in filename])

if this_week in existing_weeks:
    target_weeks = [this_week]
else:
    previous_week = tl.get_week(now - dt.timedelta(days=7))
    target_weeks = [previous_week, this_week]

# target_weeks = ['20180414', '20180421', '20180505', '20180512']
# target_weeks = ['20180519']

# 各週を出力
for week in target_weeks:
    print(week)
    time_min, time_max = GetGcalInfo.get_time_min_max(dt.datetime.strptime(week, '%Y%m%d'))
    output(time_min, time_max, week)
