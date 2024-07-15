#[title: 课表推送]
#[language: python]
#[price: 9999999]
#[service: qq群931853029]
#[disable: false]
#[admin: false]
#[rule: ^课表推送$]
#[rule: ^课表帮助$]
#[rule: ^退出推送$]
#[priority: 99999]
#[platform: wx]
#[open_source: false]
#[version: 1.0.0]
#[public: false]
#[price: 2]
#[description: 使用前先将课表导入超星学习通app，配置好时间，发送课表帮助获取具体使用。依赖安装：pip install requests，pip install cachetools，pip install mysql-connector-python或者pip install pymysql，pip install apscheduler]
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from cachetools import cached, TTLCache
import mysql.connector
import json
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import threading
from threading import Event
from mysql.connector import Error, connect
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers import SchedulerNotRunningError
import middleware
# 获取发送者ID
senderID = middleware.getSenderID()
# 创建发送者
sender = middleware.Sender(senderID)
#构建唯一ID
user=sender.getUserID()
#获取用户实时输入
content = sender.getMessage()


def customer_input1():
    customer_input2=sender.listen(6000)
    if customer_input2==None:
        sender.reply("你输入超时了,程序已退出！")
    else:
        return customer_input2

class ChaoxingAPI:
    def __init__(self, uname, passwd):
        self.session = requests.session()
        self.uname = uname
        self.passwd = passwd

    def login(self):
        url = "https://passport2-api.chaoxing.com/v11/loginregister"
        data = {
            "code": self.passwd,
            "cx_xxt_passport": "json",
            "uname": self.uname,
            "loginType": "1",
            "roleSelect": "true"
        }
        res = self.session.post(url=url, data=data).json()
        return res

    @cached(cache=TTLCache(maxsize=1, ttl=600))  # Cache login result for 10 minutes
    def get_user_info(self):
        res = self.login()
        if res["status"] == True:
            resp = self.session.get(res['url']).json()
            user_info = {
                "school": resp['msg']['schoolname'],
                "name": resp['msg']['name'],
                "phone": resp['msg']['phone']
            }
            return user_info
        else:
            return None

    def get_lessons(self):
        response = self.session.get('https://kb.chaoxing.com/pc/curriculum/getMyLessons').json()
        #print(response)        #课程信息json
        return response['data']['lessonArray']

# 登录函数
def chaoxing_login():
    sender.reply("请在60秒内输入超星学习通账号")
    #uname = sender.listen(6000)
    uname = customer_input1()
    sender.reply("请在60秒内输入密码")
    #password = sender.listen(6000)
    password = customer_input1()
    return uname, password


#数据库存储函数
def mysql_insert_and_query(user,phone,passwd,name,school,lessons_by_day):
    # 数据库连接参数
    cnx = mysql.connector.connect(
        host="8.130.122.112",
        user="kb_autman",
        password="MZxpw6xGFZCAF3Y7",
        database="kb_autman"
    )

    cursor = cnx.cursor()
    data_to_insert = {
        "user": user,
        "phone": phone,
        "passwd": passwd,
        "name": name,
        "school": school,
        "lessons_by_day": lessons_by_day,
    }

    # SQL插入语句（不包含自增主键id）
    sql_query_insert = """
        INSERT INTO customer_info (user,phone,passwd,name,school,lessons_by_day)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    # 执行插入操作
    insert_data_tuple = (
        data_to_insert["user"],
        data_to_insert["phone"],
        data_to_insert["passwd"],
        data_to_insert["name"],
        data_to_insert["school"],
        lessons_by_day,
    )
    cursor.execute(sql_query_insert, insert_data_tuple)

    # 提交事务
    cnx.commit()
    # 关闭资源
    cursor.close()
    cnx.close()

#数据库查询函数
def mysql_select_from_database(query, params=None):
    connection = mysql.connector.connect(
        host="8.130.122.112",
        user="kb_autman",
        password="MZxpw6xGFZCAF3Y7",
        database="kb_autman"
    )
    
    cursor = connection.cursor()

    try:
        # 执行SQL查询语句
        if params is not None:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        # 获取查询结果
        result_set = cursor.fetchall()
        
        return result_set  # 返回查询结果集

    finally:
        # 关闭游标和连接
        cursor.close()
        connection.close()

#查数据库信息的
def serch_database(user):
    # 定义SQL查询语句
    query = "SELECT * FROM customer_info WHERE user = %s"

    # 定义要查询的senderID值
    sender_id_to_search = user

    try:
        # 调用数据库查询函数
        result_set = mysql_select_from_database(query, (sender_id_to_search,))

        # 处理查询结果
        if result_set:
            return json.loads(result_set[0][6])
        
            

    except Error as e:
        sender.reply(f"Error occurred while connecting to the database: {e}")
        

#登录并且将信息存储到数据库
def information_storage():

    lessons_by_day_str = {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: []} 


    uname, passwd = chaoxing_login()
    chaoxing = ChaoxingAPI(uname, passwd)
    user_info = chaoxing.get_user_info()

    if user_info:
        sender.reply(f"恭喜【{user_info['name']}】登录成功,你的唯一id为：{user}")
        lessons = chaoxing.get_lessons()
        lessons_by_day_str = {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: []}
        # 遍历所有课程信息
        for lesson in lessons:
            # 提取需要的课程属性
            selected_lesson_data = {
                #'dayOfWeek': lesson[' '],                  #星期几
                'beginNumber': lesson['beginNumber'],       #第几节课
                'teacherName': lesson['teacherName'],       #老师
                'name': lesson['name'],                     #课程名称
                'location': lesson['location'],             #地点
            }
            # 将提取出所需属性的新字典添加到对应的星期列表中
            lessons_by_day_str[lesson['dayOfWeek']].append(selected_lesson_data) 
    else:
        sender.reply("登录失败，请检查账号和密码是否正确。")
    lessons_by_day = json.dumps(lessons_by_day_str)
    mysql_user_info = chaoxing.get_user_info()
    if mysql_user_info:
        school = mysql_user_info['school']
        name = mysql_user_info['name']
        phone = mysql_user_info['phone']

    mysql_insert_and_query(user,phone,passwd,name,school,lessons_by_day)

def today_data():
    weekday_mapping = {
            0: '星期一',
            1: '星期二',
            2: '星期三',
            3: '星期四',
            4: '星期五',
            5: '星期六',
            6: '星期日',
        }
    today = datetime.today()
    weekday = today.weekday()
    return weekday,weekday_mapping

#information_input 声明为全局变量：用于存储用户一周的课程信息
information_input = None

# 表示一个课程实体
class Course:
    def __init__(self, name, location, begin_number, teacher_name):
        self.name = name
        self.location = location
        self.begin_number = begin_number
        self.teacher_name = teacher_name

#获取开启定时的变量
information_input = None


class APScheduler:
    user_input_thread = None
    stop_event = Event()
    notification_time = {  # 添加一个新的定时任务
        1: (8, 0),    # 第一节课推送时间为08:00
        3: (10, 0),   # 第二节课推送时间为10:00
        5: (13, 35),  # 第三节课推送时间为13:50
        7: (15, 50),  # 第四节课推送时间为15:50
        9: (18, 30),  # 第五节课推送时间为19:10
        'all': (7, 5)  # 全部课程推送时间为07:05
    }

    def __init__(self):
        self.scheduler = BlockingScheduler()
        self.user_input_thread = None

    # 用户输入监控方法，监听用户输入以控制程序退出以及其他交互
    def user_input_monitor(self):
        global running
        while running:
            user_input = content
            if user_input and user_input.lower() == '退出':
                try:
                    sender.reply("正在关闭定时任务，请稍候...")
                    if self.scheduler.running:  # 如果调度器正在运行，则关闭它
                        self.scheduler.shutdown(wait=False)
                    sender.reply("定时任务已关闭！")
                except SchedulerNotRunningError:
                    sender.reply("调度器已经停止运行。")
                running = False  # 告诉程序的其他部分停止运行
                break


    # 课程提醒任务方法，接收一个Course对象并打印提醒信息
    def job_function(self, course):
        if not self.stop_event.is_set():
            sender.reply(f"第{(course.begin_number + 1)//2}节，课程名称：{course.name}，地点：{course.location}，教师：{course.teacher_name}")

    # 新增发送全部课程信息的任务函数
    # def send_all_courses(self):  
    #     current_weekday = datetime.now().weekday() + 1
    #     today_schedule = information_input.get(str(current_weekday), [])

    #     sender.reply("早上好！今日全部课程如下：")
    #     for course_dict in today_schedule:
    #         course = Course(
    #             course_dict["name"],
    #             course_dict["location"],
    #             course_dict["beginNumber"],
    #             course_dict["teacherName"]
    #         )
    #         begin_number = (course.begin_number + 1) // 2
    #         sender.reply((f"第{begin_number}节，课程名称：{course.name}，地点：{course.location}，教师：{course.teacher_name}"))
    def send_all_courses(self):
        current_weekday = datetime.now().weekday() + 1
        today_schedule = information_input.get(str(current_weekday), [])

        if not today_schedule:
            sender.reply("今日暂无课程安排。")
        else:
            course_messages = ["早上好！今日全部课程如下：\n"]
            for course_dict in today_schedule:
                course = Course(
                    course_dict["name"],
                    course_dict["location"],
                    course_dict["beginNumber"],
                    course_dict["teacherName"]
                )
                begin_number = (course.begin_number + 1) // 2
                course_message = f"第{begin_number}节，课程名称：{course.name}，地点：{course.location}，教师：{course.teacher_name}\n"
                course_messages.append(course_message)

            summary_message = "\n".join(course_messages)
            sender.reply(summary_message)
    # 动态添加定时任务的方法
    def add_dynamic_tasks(self, schedule_data):
        for weekday_str, today_schedule in schedule_data.items():
            for course_dict in today_schedule:
                begin_hour, begin_minute = self.notification_time.get(course_dict["beginNumber"], (0, 0))

                if begin_hour == 0 and begin_minute == 0:
                    continue
                
                course = Course(
                    course_dict["name"],
                    course_dict["location"],
                    course_dict["beginNumber"],
                    course_dict["teacherName"]
                )

                # 根据课程开始时间设置CronTrigger（这里我们以schedule_data的键作为星期）
                trigger = CronTrigger(day_of_week=str(int(weekday_str)-1), hour=begin_hour, minute=begin_minute)

                # 添加定时任务
                self.scheduler.add_job(self.job_function, trigger, args=(course,))

        # 添加每天早上7:05分发送全部课程信息的任务
        all_courses_trigger = CronTrigger(day_of_week='*', hour=self.notification_time['all'][0], minute=self.notification_time['all'][1])
        self.scheduler.add_job(self.send_all_courses, all_courses_trigger)
    def start(self):
        # 启动用户输入监控线程
        self.user_input_thread = threading.Thread(target=self.user_input_monitor)
        self.user_input_thread.start()
        
        # 启动调度器
        self.scheduler.start()

def main():
    global information_input
    global scheduler

    # 尝试从数据库获取用户课表信息
    information_input = serch_database(user=user)
    
    if information_input is None:
        # 如果没有找到课表信息，则提示用户登录
        sender.reply("未找到您的课程信息，请登录以获取课表并开启定时任务。")
        information_storage()  # 此函数负责让用户登录并将信息存入数据库
        information_input = serch_database(user=user)
        
        if information_input is None:
            sender.reply("获取课表失败，请确认您的账号和密码是否正确。")
            return

    # 如果找到课表信息，则直接开始定时任务
    sender.reply("已找到您的课程信息，现在开始为您开启定时任务。")
    try:
        scheduler = APScheduler()
        scheduler.add_dynamic_tasks(information_input)  # 添加动态定时任务
        scheduler.scheduler.start()  # 启动调度器

    except SchedulerNotRunningError:
        sender.reply("调度器未能启动。")
    except Exception as e:
        sender.reply(str(e))  # 捕获其他异常，输出异常信息


if __name__ == '__main__':
    running = True
    already_shown_help = False
    
    scheduler = None  # 初始化调度器变量
    ap_scheduler = APScheduler()
    ap_scheduler.user_input_thread = threading.Thread(target=ap_scheduler.user_input_monitor)
    ap_scheduler.user_input_thread.start()

    while running:
        if content == '课表推送':
            main()
        elif content == '课表帮助':
            if not already_shown_help:
                already_shown_help = True
                sender.reply("本程序致力于为苦逼大学生记住上课地点以及每天都上什么课，使用前先在超星学习通app内将课表导入，账号密码都是超星学习通的账号密码，程序会在每天的7：05分发送全部课程信息，如果下节课有课程序会提前20分钟发布提醒。\n使用程序的方法：发送课表推送，如果以前登录过就会直接开启推送（不用管了），如果没有是首次使用程序，发送账号密码登录，登陆成功后建议发送退出再发送课表推送开启程序（最稳妥的办法）。在程序的任何阶段发送退出都会退出程序。如果发送一次没反应请发第二次\n注意：程序仅供学习交流使用，请勿用于商业用途。\n祝您使用愉快")
        elif content == '课表退出':
            running = False
            if scheduler and scheduler.scheduler.running:
                scheduler.scheduler.shutdown(wait=False)
        
        if not running:
            break  # 如果设置为False，则退出程序