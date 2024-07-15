#[title: 搜短剧]
#[language: python]
#[class: 工具类]
#[price: 0] 
#[service: 10086]
#[disable: false]
#[admin: false]
#[rule: raw ^搜短剧\+(.*)] 
#[version: 1.0.0]版本号
#[description: 搜短剧+名称触发]
'''
pip install pymysql
pip install sqlalchemy
pip install pandas
在Title列上创建FULLTEXT索引
CREATE FULLTEXT INDEX title_fulltext_idx ON duanju_short_film (Title);
'''
import pandas as pd
from sqlalchemy import create_engine, text
import re
from pay_integral import deduct_integral  # 导入扣积分函数
import middleware

# 获取发送者ID
senderID = middleware.getSenderID()
sender = middleware.Sender(senderID)
user = sender.getUserID()
content = sender.getMessage()

# 创建数据库连接
username = 'duanju'
password = 'NjLeSXfeydZbeFWT'  # 确保密码处理得当，避免代码泄露
hostname = '8.130.122.112'
port = '3306'  # 默认MySQL端口是3306
database_name = 'duanju'

engine = create_engine(f'mysql+pymysql://{username}:{password}@{hostname}:{port}/{database_name}')

def search_by_title(title_fragment):
    query = text("""
    SELECT `Title`, `Link` 
    FROM duanju_short_film 
    WHERE MATCH (`Title`) AGAINST (:title_frag IN BOOLEAN MODE)
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"title_frag": f'%{title_fragment}%'})
        matching_rows = result.fetchall()

    if not matching_rows:
        sender.reply("未找到匹配的短剧。")
    else:
        for row in matching_rows:
            sender.reply(f"您好！您搜索的短剧《{row[0]}》的链接：{row[1]}。\n本次搜索消耗10积分")

# def main():
#     match = re.search(r"搜短剧\+([^+]*)", content)
#     if match:
#         short_film_name = match.group(1)
#         search_by_title(short_film_name)


def main():
    match = re.search(r"搜短剧\+([^+]*)", content)
    if match:
        short_film_name = match.group(1)
        
        # 在搜索前先尝试扣除积分
        if deduct_integral(user, 10):  
            search_by_title(short_film_name)
        else:
            sender.reply("抱歉，您的积分不足，无法进行搜索。")

if __name__ == '__main__':
    main()