#[title: 放假]
#[language: python]
#[price: 0] 优先级，数字越大表示优先级越高
#[service: 10086] 售后联系方式
#[disable: false] 禁用开关，true表示禁用，false表示可用
#[admin: false] 是否为管理员指令
#[rule: ^放假$]
#[rule: raw^set his_date (\d{4})年(\d{1,2})月(\d{1,2})日$]
#[open_source: true]是否开源
#[version: 1.0.0]
import re
from datetime import datetime
import os
import middleware

senderID = middleware.getSenderID()
sender = middleware.Sender(senderID)
user_id = sender.getUserID()

filename = "config/user_dates.txt"

def ensure_file_exists(filename):
    if not os.path.isfile(filename):
        with open(filename, 'w') as f:
            sender.reply(f"文件 {filename} 不存在，已自动创建")

ensure_file_exists(filename)

def has_set_reminder_date(user_id):
    try:
        with open(filename, 'r') as f:
            for line in f.readlines():
                parts = line.strip().split(',')
                if parts[0] == user_id:
                    return True
    except FileNotFoundError:
        pass

    return False

def save_reminder_date(user_id, date_obj):
    try:
        with open(filename, 'a') as f:
            formatted_date = date_obj.strftime('%Y年%m月%d日')
            f.write(f"{user_id},{formatted_date}\n")
    except Exception as e:
        sender.reply(f"尝试将用户{user_id}的日期{date_obj.strftime('%Y-%m-%d')}写入文件{filename}时发生错误: {str(e)}")

def get_saved_date(user_id):
    try:
        with open(filename, 'r') as f:
            for line in f.readlines():
                parts = line.strip().split(',')
                if parts[0] == user_id:
                    year_month_day = parts[1].split('年')
                    year = int(year_month_day[0])
                    month_day = year_month_day[1].split('月')
                    month = int(month_day[0])
                    day = int(month_day[1].split('日')[0])
                    target_date = datetime(year, month, day)
                    return target_date
    except FileNotFoundError:
        sender.reply("日期记录文件不存在。")
        return None
    sender.reply("用户 {} 尚未设置日期。".format(user_id))
    return None
def set_reminder_date(user_id, content):

    reminder_cmd_pattern = re.compile(r'set his_date (\d{4})年(\d{1,2})月(\d{1,2})日')
    match = reminder_cmd_pattern.search(content)

    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))

        target_date = datetime(year, month, day)
        save_reminder_date(user_id, target_date) 
        return target_date

    sender.reply("输入的日期格式不正确，请按照'YYYY年MM月DD日'的格式输入。")
    return None

today = datetime.today()

saved_date = get_saved_date(user_id)

is_first_time_user = not has_set_reminder_date(user_id)

if is_first_time_user:
    sender.reply(f"您好，{user_id}，检测到您是第一次使用，请在60秒内设置日期（格式：set his_date x年x月x日）")
    content = sender.listen(60000)

    new_date = set_reminder_date(user_id, content)
    if new_date is not None:
        today = datetime.today()
        days_diff = (new_date - today).days
        
        if days_diff > 0:
            sender.reply(f"成功设置提醒，用户{user_id}，距离您设置的{new_date.strftime('%Y年%m月%d日')}还有{days_diff}天")
        elif days_diff < 0:
            past_days = abs(days_diff)
            sender.reply(f"距离您设置的{new_date.strftime('%Y年%m月%d日')}已经过去{past_days}天")
        else:
            sender.reply(f"距离您设置的日期就是今天！")
    else:
        sender.reply("您输入的日期格式不正确或尚未指定日期。请按照 'set his_date YYYY年MM月DD日' 的格式输入。")
else:
    if saved_date is not None:
        days_diff = (saved_date - today).days

        if days_diff > 0:
            sender.reply(f"距离您设置的{saved_date.strftime('%Y年%m月%d日')}还有{days_diff}天")
        else:
            past_days = abs(days_diff)
            sender.reply(f"距离您设置的{saved_date.strftime('%Y年%m月%d日')}已经过去{past_days}天")