# -*-coding:utf-8 -*-

"""
@author: hanke
@date: 2024/9/1 16:07
"""

import yaml
import datetime
import sys
import pytz
import numpy as np
import pandas as pd

from builtins import input
from collections import OrderedDict
from sqlalchemy import create_engine
from sqlalchemy import Column, String, Float, Integer, insert, inspect, MetaData, Table
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.mysql import insert  # MySQL的特定插入操作

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from yaml.representer import SafeRepresenter
_mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG


def dict_representer(dumper, data):
    return dumper.represent_dict(data.iteritems())


def dict_constructor(loader, node):
    return OrderedDict(loader.construct_pairs(node))


Dumper.add_representer(OrderedDict, dict_representer)
Loader.add_constructor(_mapping_tag, dict_constructor)

Dumper.add_representer(str, SafeRepresenter.represent_str)


def ordered_dump(data, stream=None, Dumper=yaml.Dumper, **kwds):
    class OrderedDumper(Dumper):
        pass

    def _dict_representer(dumper, data):
        return dumper.represent_mapping(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items())

    OrderedDumper.add_representer(OrderedDict, _dict_representer)
    return yaml.dump(data, stream, OrderedDumper, **kwds)


# Helper function for yes no questions
def query_yes_no(question, default="no"):
    """Ask a yes/no question via input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def sort_yamldata(yaml_file, sorted_yaml_file):
    dateformat = '%Y-%m-%d %H:%M:%S'
    tba_words = ["tba", "tbd"]

    right_now = datetime.datetime.utcnow().replace(microsecond=0).strftime(dateformat)
    with open(yaml_file, 'r') as stream:
        try:
            data = yaml.load(stream, Loader=Loader)
            # print("Initial Sorting:")
            # for q in data:
            #     print(q["deadline"], " - ", q["title"])
            # print("\n\n")
            conf = [x for x in data if str(x['deadline']).lower() not in tba_words]
            tba = [x for x in data if str(x['deadline']).lower() in tba_words]

            # just sort:
            conf.sort(key=lambda x: pytz.utc.normalize(datetime.datetime.strptime(x['deadline'], dateformat).replace(tzinfo=pytz.timezone(x['timezone'].replace('UTC+', 'Etc/GMT-').replace('UTC-', 'Etc/GMT+')))))
            print("Date Sorting:")

            for q in conf + tba:
                print(q["deadline"], " - ", q["title"])
            print("\n\n")
            # conf.sort(key=lambda x: pytz.utc.normalize(datetime.datetime.strptime(x['deadline'], dateformat).replace(tzinfo=pytz.timezone(x['timezone'].replace('UTC+', 'Etc/GMT-').replace('UTC-', 'Etc/GMT+')))).strftime(dateformat) < right_now)
            # print("Date and Passed Deadline Sorting with tba:")
            # for q in conf + tba:
            #     print(q["deadline"], " - ", q["title"])
            # print("\n\n")

            with open(sorted_yaml_file, 'w') as outfile:
                for line in ordered_dump(
                        conf + tba,
                        Dumper=yaml.SafeDumper,
                        default_flow_style=False,
                        explicit_start=True).splitlines():
                    outfile.write(line.replace('- title:', '\n- title:'))
                    outfile.write('\n')
        except yaml.YAMLError as exc:
            import pdb;pdb.set_trace()
            print(exc)

def add_yaml2excel(yaml_file, excel_file, excel_file_out):
    # 根据会议只保留最新的两个数据，最新的排第一个位置
    with open(yaml_file, 'r') as stream:
        data = yaml.load(stream, Loader=Loader)

    ccf_df = pd.read_excel(excel_file)
    ccf_short_names = ccf_df['刊物简称'].str.strip().str.lower().tolist()
    res_dict = {}
    # 根据会议简称来匹配
    for x in data:
        conference_name = x['title']
        conference_name = conference_name.strip().lower()
        if conference_name not in ccf_short_names:
            continue
        if conference_name not in res_dict:
            res_dict[conference_name] = x
        else:
            year_old = res_dict[conference_name]['year']
            year_new = x['year']
            if year_new > year_old:
                res_dict[conference_name] = x
    print(len(res_dict.keys()), res_dict.keys())

    # Update the corresponding positions in the original Excel file
    for conference_name, conf_data in res_dict.items():

        # Find the matching row index in the original DataFrame
        idx = ccf_df[ccf_df['刊物简称'].str.strip().str.lower() == conference_name].index

        # If a matching row is found, update the information in that row
        if not idx.empty:
            for key, value in conf_data.items():
                if key in ccf_df.columns:
                    ccf_df.at[idx[0], key] = value
                else:
                    # If the column does not exist in the DataFrame, add a new column
                    ccf_df.loc[idx[0], key] = value

    # Save the updated Excel file
    with pd.ExcelWriter(excel_file_out, mode='w', engine='openpyxl') as writer:
        ccf_df.to_excel(writer, index=False)

    return res_dict


def write_excel2mysql(excel_file, column_mapping, sheet_name='final', table_name="ai_conferences", years=[2023,2024,2025]):
    # 示例配置
    # todo 更改成自己的数据库链接
    mysql_config = {
        'user': 'user',
        'password': 'password',
        'host': 'host',
        'port': "port",
        'database': 'dbname'
    }

    # 读取Excel文件中的数据
    df = pd.read_excel(excel_file, sheet_name=sheet_name)

    # 将非符合年份的数据字段清空，只保留title
    if years:
        df['year_valid'] = df['year'].isin(years)
        for col in df.columns:
            if col != 'title' and col != 'year' and col != 'year_valid':
                df.loc[~df['year_valid'], col] = None

        # 删除辅助列
        df.drop(columns=['year_valid'], inplace=True)
        # 对timezone进行转换转换为utc_0, 'deadline_utc0','abstract_deadline_utc0'
        # 定义一个函数来处理时间和时区
        # 定义一个函数来处理时间和时区
        def convert_to_utc(row, row_name):
            if pd.isnull(row[row_name]) or pd.isnull(row['timezone']):
                return None
            try:
                # 处理常见的时区格式
                tz = row['timezone']
                if tz.lower() == 'utc':
                    tz = pytz.FixedOffset(0 * 60)
                elif tz.startswith('UTC'):
                    hours_offset = int(tz[3:])
                    tz = pytz.FixedOffset(hours_offset * 60)
                else:
                    tz = pytz.timezone(tz)

                # 转换为 UTC
                return pd.to_datetime(row[row_name]).tz_localize(tz).tz_convert('UTC')
            except Exception as e:
                print(f"Error converting row: {row}, Error: {e}")
                return None

        # 应用函数，将时间转换为 UTC
        df['deadline_utc'] = df.apply(convert_to_utc, axis=1, row_name='deadline')
        df['abstract_deadline_utc'] = df.apply(convert_to_utc, axis=1, row_name='abstract_deadline')

    # 字段选择和映射
    df = df[list(column_mapping.keys())]  # 选择需要的列
    df.rename(columns=column_mapping, inplace=True)  # 重命名列

    # 使用PyMySQL创建MySQL数据库连接
    engine = create_engine(
        f"mysql+pymysql://{mysql_config['user']}:{mysql_config['password']}@{mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}?charset=utf8mb4")
    connection = engine.connect()

    def add_columns_to_table(engine, table_name, new_columns):
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=engine)
        for col in new_columns:
            # 假设所有新列都是字符串类型，如果需要处理其他数据类型，可以在这里进行修改
            new_column = Column(col, String)  # 或者使用其他类型，比如 Integer, Float, DateTime 等
            new_column.create(table, populate_default=True)
        metadata.create_all(engine)

    def upsert_data(engine, df, table_name):
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=engine)

        # Replace NaN with None (to insert as NULL in MySQL)
        df = df.replace({np.nan: None})

        with engine.connect() as conn:
            for index, row in df.iterrows():
                insert_stmt = insert(table).values(row.to_dict())
                update_stmt = insert_stmt.on_duplicate_key_update(
                    {col: getattr(insert_stmt.inserted, col) for col in row.keys()}
                )
                conn.execute(update_stmt)

    try:
        # 检查表是否存在
        if not inspect(engine).has_table(table_name):
            # 表不存在，创建新表并插入数据
            df.to_sql(name=table_name, con=engine, if_exists='fail', index=False)
            print(f"Table '{table_name}' created and data inserted successfully.")
        else:
            # 表存在，获取表结构并处理新列
            existing_table = Table(table_name, MetaData(), autoload_with=engine)
            existing_columns = existing_table.columns.keys()

            # 检查并处理新列
            new_columns = [col for col in df.columns if col not in existing_columns]
            if new_columns:
                # 手动新增新列到表中
                add_columns_to_table(engine, table_name, new_columns)
                print(f"New columns {new_columns} added to the table '{table_name}'.")

            # 进行数据的插入或更新操作
            upsert_data(engine, df, table_name)
            print(f"Data upserted to existing table '{table_name}'.")

    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")

    finally:
        connection.close()

if __name__ == '__main__':
    # 1. 对yaml_file格式统一检查，并且排序,得到sorted_yaml_file
    yaml_file = "../data/conferences.yml"
    sorted_yaml_file = '../data/sorted_data.yml'
    # sort_yamldata(yaml_file, sorted_yaml_file)

    # 2. 将外部别人收集的数据sorted_yaml_file, 更新之前手动清理的得到out_excel_path1,最后得到excel_file_out
    yaml_file = '../data/sorted_data.yml'
    excel_file = 'final_entries_1.xlsx'
    excel_file_out = 'final_entries_out.xlsx'
    # add_yaml2excel(yaml_file, excel_file, excel_file_out)

    # 3. 最后进行rank和rank_notes的逻辑整理，将更新的数据excel_file_out写入mysql库中
    table_name = 'ai_conferences'
    # 字段映射 (Excel列名 -> MySQL列名)
    column_mapping = {
        '刊物简称': 'name',
        '刊物全称_CAAI': 'name_long',
        '等级_CCF': 'rank_ccf',
        '等级_CAAI': 'rank_caai',
        '分类_CAAI': 'tags',
        '出版社_CAAI': 'publication',
        '网址_CAAI': 'link_caai',
        '来源_CAAI': 'source',
        "rank":"rank",
        "rank_notes":"rank_notes"
    }

    table_name1 = 'ai_conference_year'
    # 字段映射 (Excel列名 -> MySQL列名)
    column_mapping1 = {
        'title': 'name',
        'year': 'year',
        'deadline': 'deadline',
        'deadline_utc': 'deadline_utc',
        'abstract_deadline': 'abstract_deadline',
        'abstract_deadline_utc': 'abstract_deadline_utc',
        'date': 'date',
        'start': 'start',
        'end': 'end',
        'place': 'place',
        'timezone': 'timezone',
        'link': 'link',
        'paperslink': 'paperslink',
        'pwclink': 'pwclink',
        'note': 'note'
    }

    # 调用函数
    excel_file = 'final_entries_out.xlsx'
    sheet_name = 'final'  # 如果有特定的工作表名称

    # write_excel2mysql(excel_file, column_mapping, sheet_name, table_name, years=[])
    # write_excel2mysql(excel_file, column_mapping1, sheet_name, table_name1, years=[2023,2024,2025])
