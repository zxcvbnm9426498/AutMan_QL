#[title: 小工具]
#[language: python]
#[price: 0] 优先级，数字越大表示优先级越高
#[service: 2] 售后联系方式
#[disable: false] 禁用开关，true表示禁用，false表示可用
#[admin: false] 是否为管理员指令
#[rule: raw ^计算(\d{1,2})月(\d{1,2})日到(\d{1,2})月(\d{1,2})日$]
#[rule: ^窝囊费$]
#[priority: 0] 优先级，数字越大表示优先级越高
#[platform: wx] 适用的平台
#[open_source: true]是否开源
#[price: 999] 上架价格
#[description: 计算日期差]
import middleware
import re
from datetime import datetime, timedelta
import calendar

# 获取发送者ID
senderID = middleware.getSenderID()
# 创建发送者
sender = middleware.Sender(senderID)
#获取用户的唯一id
user=sender.getUserID()
#获取用户输入
content = sender.getMessage()

#计算日期差函数
def calculate_date_difference(match):

    if not match:
        sender.reply("输入格式不正确，请按照 '计算x月x日到x月x日' 的格式输入。")
        return
    
    # 解析日期
    start_month, start_day, end_month, end_day = map(int, match.groups())
    current_year = datetime.now().year  # 假设日期为当前年份
    try:
        start_date = datetime(current_year, start_month, start_day)
        end_date = datetime(current_year, end_month, end_day)
        
        if start_date > end_date:
            # 如果起始日期在结束日期之后，假设是跨年
            end_date = datetime(current_year + 1, end_month, end_day)
        
        # 计算日期差
        date_diff = end_date - start_date
        days_diff = date_diff.days
        sender.reply(f"相差 {days_diff+1} 天")

    except ValueError:
        sender.reply("输入的日期不正确，请确保月份和日期有效。")

#计算每个月到27号剩余天数函数
def count_days_and_weekends_to_next_27th():
    try:
        today = datetime.today()

        # 获取当前月份和年份
        current_month = today.month
        current_year = today.year

        # 确定下一个27号所在的日期（如果本月已过27号，则为下个月的27号）
        target_date = datetime(current_year, current_month, 27)
        if target_date < today:
            # 跳至下个月
            target_date = target_date.replace(month=target_date.month + 1)

        days_to_target = (target_date - today).days + 1  # 加1是因为包含今天的天数

        # 初始化周末计数器
        weekends_count = 0
        for day in range(days_to_target):
            temp_date = today + timedelta(days=day)
            weekday = temp_date.weekday()
            if weekday == 6:  # Python中周一到周日对应0-6，所以这里是周五和周六
                weekends_count += 1

        return days_to_target, weekends_count

    except Exception as e:
        return f"计算失败，原因：{str(e)}"

def main():
    date_pattern = re.compile(r"计算(\d{1,2})月(\d{1,2})日到(\d{1,2})月(\d{1,2})日")
    match = date_pattern.search(content)
    if match:
        calculate_date_difference(match)
    elif content == "窝囊费":
        # 调用函数并输出结果
        result = count_days_and_weekends_to_next_27th()
        if isinstance(result, tuple):
            days_remaining, weekends_in_between = result
            sender.reply(f"距离下个27号还有{days_remaining+1}天，其中包括{weekends_in_between}个周末。")
        else:
            sender.reply(result)
if __name__ == '__main__':
    main()