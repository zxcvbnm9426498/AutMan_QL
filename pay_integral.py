#[title: 收款]
#[language: python]
#[admin: false] 是否为管理员指令
#[rule: ^消费$]
#[rule: ^查询$]

"""
sql：
USE pay_integral;

CREATE TABLE `pay_integral.customer_pay_integral` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `userid` VARCHAR(255) NOT NULL UNIQUE,
    `integral` VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
"""

import json
import time
import mysql.connector
import middleware
# 获取消息发送者ID及实例化Sender对象
senderID = middleware.getSenderID()
sender = middleware.Sender(senderID)
user = sender.getUserID()
content = sender.getMessage()

DB_CONFIG = {
    "host": "8.130.122.112",
    "user": "pay_integral",
    "password": "Jcap66xjKGwT24H3",
    "database": "pay_integral"
}

# 连接数据库函数
def connect_to_db():
    return mysql.connector.connect(**DB_CONFIG)

# 更新用户积分函数，增加指定金额对应的积分值
def update_user_integral(userid, amount):
    # 将金额转换为对应积分（假设1元=100分）
    integral_to_add = int(amount * 100)
    
    # 连接数据库并执行查询语句获取用户当前积分
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute("SELECT integral FROM customer_pay_integral WHERE userid = %s", (userid,))
    result = cursor.fetchone()

    # 如果存在用户记录，则更新积分；否则插入新记录
    if result:
        new_integral = int(result[0]) + integral_to_add
        cursor.execute("UPDATE customer_pay_integral SET integral = %s WHERE userid = %s", (str(new_integral), userid))
    else:
        cursor.execute("INSERT INTO customer_pay_integral (userid, integral) VALUES (%s, %s)", (userid, integral_to_add))

    # 提交事务并关闭游标与数据库连接
    connection.commit()
    cursor.close()
    connection.close()

# 查询用户积分函数
def query_user_integral(userid):
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute("SELECT integral FROM customer_pay_integral WHERE userid = %s", (userid,))
    result = cursor.fetchone()
    # 关闭游标与数据库连接，并返回查询结果（积分值）
    cursor.close()
    connection.close()
    if result:
        return result[0]
    else:
        return None

# 发送收款凭证图片函数
def send_receipt_image(sender):
    try:
        sender.replyImage("http://8.130.122.112:8080/admin/images/gallery/1709198542140735497.jpg")
    except Exception as e:
        sender.reply("抱歉，发生了错误，无法发送收款图片。")
        #sender.reply("Error sending image:", e)

# 处理支付请求函数
def handle_payment(sender, user):
    # 先发送收款凭证图片
    send_receipt_image(sender)
    
    # 设置退出码和超时时间
    exit_code = "q"
    timeout = 120000

    try:
        # 等待接收支付响应
        payment_response = sender.waitPay(exit_code, timeout)
        
        if payment_response == exit_code:  # 检查是否为用户输入的退出指令
            sender.reply("程序已退出支付等待。")
            return
        
        payment_info = json.loads(payment_response) if isinstance(payment_response, str) else payment_response
        confirm_payment(sender, user, payment_info)

    except TimeoutError:
        sender.reply("支付等待超时，程序已退出支付流程。")

    except Exception as e:
        sender.reply("抱歉，处理您的打赏时发生了异常。")
        #sender.reply("Error processing payment:", e)
#扣除积分函数
def deduct_integral(userid, amount):
    # 这里假设扣除10积分
    if amount == 10:
        update_user_integral(userid, -amount / 100)  # 将金额转为负数以便扣除积分
        return True
    else:
        return False  # 扣除积分失败或不满足条件时返回False


# 确认并更新用户积分函数
def confirm_payment(sender, user, payment_info):
    actual_amount = payment_info.get("Money", 0)
    from_name = payment_info.get("FromName", "")
    
    # 如果实际支付金额大于0，则更新积分
    if actual_amount > 0:
        update_user_integral(user, actual_amount)
        sender.reply(f"感谢{from_name}的打赏，金额为{actual_amount}元，您获得了{int(actual_amount * 100)}积分。")
    else:
        sender.reply("未能收到打赏，请确认打赏操作已完成。")

# 主函数：根据用户指令执行相应操作
def main():

    # 判断用户输入指令
    if content.lower() == "消费":
        sender.reply("请在120秒内扫码支付充值金额。")
        time.sleep(1)  # 延迟一秒以确保用户看到消息
        handle_payment(sender, user)
    elif content.lower() == "查询":
        integral = query_user_integral(user)
        if integral is not None:
            sender.reply(f"您当前的积分余额为：{integral}分。")
        else:
            sender.reply("您当前没有积分记录。")

if __name__ == "__main__":
    main()