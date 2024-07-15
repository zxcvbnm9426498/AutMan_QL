#[title: 待办提醒]
#[language: python]
#[price: 0]
#[service: 230047029]售后联系方式
#[disable: false]
#[admin: false]
#[rule: raw ^提醒\+(.*)] 
#[rule: ^提醒列表$]
#[rule: ^待办帮助$]
#[priority: 0] 优先级，数字越大表示优先级越高
#[platform: qq,qb,wx,tb,tg,web,wxmp]
#[open_source: false]是否开源
#[version: 1.0.1]
#[public: true]
#[price: 1] 上架价格
#[description: 本插件旨在提醒用户做某件事情，并在指定时间提醒用户。指令：提醒+时间 内容。时间格式：n分钟后、n小时后、n小时m分后、n天后、n月d日h点m分、周x h点m分、星期x h点m分、明天h点m分、后天h点m分、h点m分。例如：提醒10分钟后吃饭。提醒列表：查看当前用户的待办事项。程序会在第一次运行创建一个config文件夹，并在其中创建todo_list.txt文件，用于存储用户的待办事项。如果任务执行了程序会在txt中删除对应的任务。txt写入格式：udser_id,时间,事件。依赖安装：pip install apscheduler，pip install python-dateutil]
#[description:1.添加依赖安装说明。2.修复脚本目录没有config文件夹报错。3.新增用户界面的使用说明：^待办帮助$]
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from datetime import datetime, timedelta
from dateutil import parser
import re
import time
from apscheduler.events import JobEvent
from dateutil.parser import parse
import locale
import os
import middleware
# 获取发送者ID
senderID = middleware.getSenderID()
# 创建发送者
sender = middleware.Sender(senderID)
#获取用户的唯一id
user=sender.getUserID()

content = sender.getMessage()

#全局停止变量
is_running = True

locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')

# 创建后台调度器并启动
scheduler = BackgroundScheduler()
scheduler.start()

# 定义待办事项文件路径
TODO_FILE = "config/todo_list.txt"

def load_todo_list():
    global todo_list
    TODO_FILE = "config/todo_list.txt"
    
    if not os.path.exists('config'):
        os.makedirs('config')  # 创建config文件夹
        sender.reply("系统检测到您还没有创建待办事项文件，已为您创建待办事项文件。")
        # 文件不存在，则创建新文件
        open(TODO_FILE, 'w', encoding='utf-8').close()
        todo_list = {}
    else:
        with open(TODO_FILE, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            todo_list = {}
            for line in lines:
                user_id, remind_time_str, action = line.strip().split(',')
                remind_time = parser.parse(remind_time_str)
                todo_list[user_id] = {'time': remind_time, 'action': action}
                
    return todo_list

def save_todo_list(todo_list):
    #print(f"Saving todo list: {todo_list}")
    with open(TODO_FILE, 'w', encoding='utf-8') as file:
        for user_id, info in todo_list.items():
            file.write(f"{user_id},{info['time'].strftime('%Y-%m-%d %H:%M:%S')},{info['action']}\n")

# 创建定时提醒的函数
def schedule_once(time_str, action):
    now = datetime.now()
    
    weekdays_map = {
        '一': 0,
        '二': 1,
        '三': 2,
        '四': 3,
        '五': 4,
        '六': 5,
        '日': 6,
        '天': 6
    }

    # 定义下一个特定天数后的特定时间
    def get_next_day_time(days, hour, minute):
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days)
        return target_time
    
    def next_weekday(now, weekday_str, hour, minute):
        target_weekday = weekdays_map[weekday_str]  # 使用字典转换
        days_ahead = (target_weekday - now.weekday() + 7) % 7
        if days_ahead == 0 and (now.hour > hour or (now.hour == hour and now.minute >= minute)):
            days_ahead += 7
        next_date = now + timedelta(days=days_ahead)
        return datetime(next_date.year, next_date.month, next_date.day, hour, minute)
    
    # 时间逻辑处理
    patterns = [
        (r'(\d+)分钟后', lambda amount: now + timedelta(minutes=int(amount))),
        (r'(\d+)小时后', lambda amount: now + timedelta(hours=int(amount))),
        (r'(\d+)小时(\d+)分后', lambda hour, minute: now + timedelta(hours=int(hour), minutes=int(minute))),
        (r'(\d+)天后', lambda amount: now + timedelta(days=int(amount))),
        (r'(\d+)月(\d+)日(\d+)点(\d+)分', lambda month, day, hour, minute:
            datetime(now.year, int(month), int(day), int(hour), int(minute))),
        (r'周(.)\s*(\d+)点(\d+)分', lambda weekday, hour, minute: 
            next_weekday(now, weekday, int(hour), int(minute))),
        (r'星期(.)\s*(\d+)点(\d+)分', lambda weekday, hour, minute: 
            next_weekday(now, weekday, int(hour), int(minute))),
        (r'明天(\d+)点(\d+)分', lambda hour, minute:
            get_next_day_time(1, int(hour), int(minute))),
        (r'后天(\d+)点(\d+)分', lambda hour, minute:
            get_next_day_time(2, int(hour), int(minute))),
        (r'(\d+)点(\d+)分', lambda hour, minute:
            now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0))
    ]
    
    remind_time = None

    # 查找与时间表达式匹配的模式
    for pattern, time_logic in patterns:
        match = re.search(pattern, time_str)
        if match:
            remind_time = time_logic(*match.groups())
            break

    if not remind_time or remind_time <= now:
        print("无法解析时间，或者时间设置在了过去。请输入有效的时间描述。")
        return False

    if remind_time < now:
        sender.reply("不能设置在过去的时间提醒。")
        return False

    else:
        job = scheduler.add_job(reminder_job, 'date', run_date=remind_time, args=[action])
        #todo_list[job.id] = {'time': remind_time, 'action': action}
        #sender.reply(f"提醒已设置在 [{remind_time.strftime('%Y-%m-%d %H:%M:%S')}]，内容是：{action}")
        return True

 # 查看待办列表的函数
def view_todo_list():
    if not todo_list:
        sender.reply("当前没有待办事项。")
        return

    todo_list_message = "当前待办列表如下：\n"
    for user, info in todo_list.items():
        todo_list_message += f"时间: {info['time'].strftime('%Y-%m-%d %H:%M:%S')}, 待办事项: {info['action']}\n"

    sender.reply(todo_list_message)

# 提醒任务执行函数
def reminder_job(action):
    sender.reply(f"时间到了！您该去{action}了。")
    for user, info in todo_list.items():
        if info['action'] == action:
            # 执行完后从待办事项中移除
            del todo_list[user]
            break

# 事件监听器函数
def reminder_listener(event):
    if event.exception:
        sender.reply('提醒任务出错了!')
        sender.reply(f"错误详情：{event.exception}")

# 将用户的提醒添加到调度器中
def add_reminder_to_scheduler(time_str, action):
    # 新增加载待办事项列表和保存待办事项列表的功能
    global todo_list

    if not schedule_once(time_str, action):
        sender.reply("抱歉，无法设置提醒。请检查您的时间格式是否正确。")
        return False

    # 添加待办事项到全局todo_list中，并保存到文件
    job = scheduler.get_jobs()[-1] 
    todo_list[user] = {'time': job.next_run_time, 'action': action}
    save_todo_list(todo_list)

    sender.reply(f"提醒已设置在 [{job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')}]，内容是：{action}")
    return True


last_handled_message_id = None  # 定义一个变量来记录上次处理过的消息ID
# 正确地匹配并提取提醒时间和内容的正则表达式
reminder_cmd_pattern = re.compile(r"提醒\+([\s\S]+)\s+(.+)")

# 主函数
def main():
    global is_running, scheduler
    last_handled_message = None  # 用以记录上一次处理过的消息内容
    # 获取用户输入
    content = sender.getMessage()
    #current_message_id = sender.getMessageID()  # 获取当前消息ID
    while is_running:
        # 检查是否接收到了新的内容，并且内容与上一次处理的不同
        if content is not None and content != last_handled_message:
            match = reminder_cmd_pattern.search(content)
            if match:
                time_str, action = match.groups()
                add_reminder_to_scheduler(time_str, action)
            elif content == '提醒列表':
                view_todo_list()
            elif content == '待办帮助':
                sender.reply("插件旨在提醒用户做某件事情，并在指定时间提醒用户。指令：提醒+时间 内容。时间格式：n分钟后、n小时后、n小时m分后、n天后、n月d日h点m分、周x h点m分、星期x h点m分、明天h点m分、后天h点m分、h点m分。例如：提醒10分钟后吃饭。提醒列表：查看当前用户的待办事项。")
            else:
                sender.reply("未知指令，请重新输入。")
            last_handled_message = content  # 更新最后处理过的消息内容
        # 短暂休眠以避免CPU占用过高
        time.sleep(1)


# 创建定时任务执行完成后的事件监听逻辑
def my_listener(event):
    global is_running
    if not isinstance(event, JobEvent):
        return
    # 作业执行完毕的事件
    if event.code == EVENT_JOB_EXECUTED or event.code == EVENT_JOB_ERROR:
        # 当执行完一个作业时检查作业列表
        if not scheduler.get_jobs():
            # 没有作业了，发送消息并关闭调度器
            #sender.reply("所有提醒任务已执行完毕，程序已经退出。")
            is_running = False
            scheduler.shutdown(wait=False)  # 立即停止调度器，不等待剩余的作业完成

    
# 添加监听器
scheduler.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

if __name__ == "__main__":
    # 在主函数开始前加载待办事项列表，并将其赋值给全局变量todo_list
    todo_list = load_todo_list()

    try:
        main()
    except Exception as e:
        sender.reply(f"程序遇到错误并即将退出：{e}")
        scheduler.shutdown()
    finally:
        save_todo_list(todo_list)