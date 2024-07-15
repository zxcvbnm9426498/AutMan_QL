#[title: 课表更新]
#[language: python]
#[price: 9999999]
#[service: 23004777029]
#[disable: false]
#[admin: false]
#[rule: ^kbgx$]
#[cron: 0 1 * * 1]
#[priority: 99999]
#[platform: wx]
#[open_source: false]
#[version: 1.0.0]
#[public: false]
#[price: 0.01]
#[description: 每周一晚上对课表进行更新]
from kbcj import ChaoxingAPI
import mysql.connector
import json
import middleware

# 获取发送者ID
senderID = middleware.getSenderID()
sender = middleware.Sender(senderID)
user = sender.getUserID()

# 数据库连接
cnx = mysql.connector.connect(
    host="8.130.122.112",
    user="kb_autman",
    password="MZxpw6xGFZCAF3Y7",
    database="kb_autman"
)
cursor = cnx.cursor()

# 更新lessons_by_day函数，返回是否成功
def mysql_update_lessons_by_day(name, phone, lessons_by_day):
    try:
        sql_query_update = """
            UPDATE customer_info
            SET lessons_by_day = %s
            WHERE phone = %s
        """
        update_data_tuple = (lessons_by_day, phone)
        cursor.execute(sql_query_update, update_data_tuple)
        cnx.commit()
        return True
    except Exception as e:
        print(f"更新课表时出错: {e}")
        return False

# 查询所有不重复的账号密码
def query_unique_phone_and_passwd(cursor):
    sql_query = "SELECT DISTINCT phone, passwd FROM customer_info"
    cursor.execute(sql_query)
    unique_phone_password_pairs = cursor.fetchall()
    return unique_phone_password_pairs

summary_message = f"共获取到{len(query_unique_phone_and_passwd(cursor))}个账号。\n"

success_count = 0
for pair in query_unique_phone_and_passwd(cursor):
    uname, passwd = pair[0], pair[1]
    chaoxing = ChaoxingAPI(uname, passwd)

    if chaoxing.login():
        login_success_message = f"【{chaoxing.get_user_info()['name']}】登录成功\n"
        lessons = chaoxing.get_lessons()
        lessons_by_day_str = {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: []}

        for lesson in lessons:
            selected_lesson_data = {
                'beginNumber': lesson['beginNumber'],
                'teacherName': lesson['teacherName'],
                'name': lesson['name'],
                'location': lesson['location'],
            }
            lessons_by_day_str[lesson['dayOfWeek']].append(selected_lesson_data)

        lessons_by_day = json.dumps(lessons_by_day_str)
        if mysql_update_lessons_by_day(chaoxing.get_user_info()['name'], uname, lessons_by_day):
            success_count += 1
            summary_message += f"【{uname}】的课表更新成功！\n"
        else:
            summary_message += f"【{uname}】的课表更新失败！\n"
    else:
        failed_login_message = f"{uname}登录失败\n"
        summary_message += failed_login_message + "\n"

# 关闭数据库连接
cursor.close()
cnx.close()

# 发送汇总消息
if sender.getImtype() == "fake":
    middleware.notifyMasters("定时任务" + summary_message)
else:
    sender.reply(summary_message if success_count > 0 else "部分或全部用户课表更新失败，请检查日志")