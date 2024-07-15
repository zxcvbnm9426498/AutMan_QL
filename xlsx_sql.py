import pandas as pd
import re
from sqlalchemy import create_engine
from sqlalchemy import inspect

# 创建MySQL数据库连接
username = 'duanju'
password = 'NjLeSXfeydZbeFWT'  # 请确保密码处理得当，避免代码泄露
hostname = '8.130.122.112'
port = '3306'  # 默认MySQL端口是3306
database_name = 'duanju'
table_name = 'duanju_short_film'

def xlsx_sql():
    # 读取Excel文件
    file_path = '短剧.xlsx'
    df = pd.read_excel(file_path, sheet_name='Sheet1')

    # 确保列名正确（根据实际情况调整）
    df.columns = ['序号', '原始标题', '链接']

    # 预处理标题列内容并重命名列以匹配数据库表结构
    df['Title'] = df['原始标题'].apply(lambda x: re.sub(r'\d+\.\s*|\(\d+\集\)', '', x))
    df = df.rename(columns={'链接': 'Link'})  # 将'链接'列名改为'Link'
    df = df[['Title', 'Link']] 

    # 构建数据库引擎字符串
    engine = create_engine(f'mysql+pymysql://{username}:{password}@{hostname}:{port}/{database_name}')

    n = 1
    # 将数据写入数据库并打印已保存的标题
    for index, row in df.iterrows():
        title = row['Title']
        data_to_save = df.iloc[index:index+1]  # 获取当前行数据
        data_to_save.to_sql(table_name, con=engine, if_exists='append', index=False)
        print(f"第{n}部短剧：{title} 已保存到数据库")
        n += 1

    print("所有数据已成功导入到MySQL数据库中!")


