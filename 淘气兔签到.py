'''

Author: Zanet

Creat_time: 2024-07-08 09:02

Function: 
    环境变量：emailandpasswordandpushplus_tokenandduihuan：邮箱,密码,plus_token,True or False:如果想兑换就填True，否则填False
    签到淘气兔VPN流量,每天执行一次，签到可以抵消流量
    环境变量：邮箱,密码,pushplus_token
    官网地址：https://vip.taoqitu.pro/index.html?register=gwmhHs0Z

Version: 1.0.1
    更新内容：增加兑换功能，通过True和False来控制是否兑换，True为兑换，False为不兑换。
             然后就是变量名又长了

'''

import requests
import os

url_dict = {
    'login':'https://api-cdn.taoqitu.me/gateway/tqt/cn/passport/auth/login',
    'sign':'https://api-cdn.taoqitu.me/gateway/tqt/cn/user/sign',
    'getSignList':'https://api-cdn.taoqitu.me/gateway/tqt/cn/user/getSignList',
    'duihuan':'https://api-cdn.taoqitu.me/gateway/tqt/cn/user/convertSign',
}

def login(url, email, password):
    params = {
        'email': email,
        'password': password,
    }

    response = requests.post(url, data=params)
    json_response = response.json()
    if json_response:
        return json_response
    else:
        return None

def sign(url, Authorization):
    headers_sign = {
        'Authorization': Authorization,
    }

    response = requests.get(url, headers=headers_sign)
    json_response = response.json()
    message = json_response.get('message')
    return message

def getSignList(url, Authorization):
    headers_getSignList = {
        "Authorization": Authorization,
    }

    response = requests.get(url, headers=headers_getSignList)
    data = response.json()
    today_data = data['data'][0]['get_num']
    return today_data

def send_push_notification(message, pushplus_token):
    pushplus_url = f"http://www.pushplus.plus/send?token={pushplus_token}"

    data = {
        "title": "淘气兔签到通知！",
        "content": message,
    }

    response = requests.post(pushplus_url, json=data)
    if response.status_code == 200:
        print("消息推送成功！")
    else:
        print("消息推送失败！")

def duihuan(Authorization, convert_num):
    headers_duihuan = {
        'Authorization': Authorization,
    }

    params_duihuan = {
        'convert_num': convert_num,
    }

    response = requests.get(url_dict['duihuan'], headers=headers_duihuan, params=params_duihuan)
    if response.status_code == 200:
        messaage1 = response.json().get('message')
        return messaage1
    else:
        messaage1 = f"兑换失败，请检查{Authorization}是否正确！"
        return messaage1

if __name__ == '__main__':
    email, password, pushplus_token, duihuan_flag = os.environ['emailandpasswordandpushplus_tokenandduihuan'].split(',')
    login_data = login(url_dict['login'], email, password)
    if login_data is not None:
        Authorization = login_data['data']['auth_data']
        message = sign(url_dict['sign'], Authorization)
        today_data = getSignList(url_dict['getSignList'], Authorization)
        if duihuan_flag == 'True':
            messaage1 = duihuan(Authorization, float(today_data))
            message = f"{email}登陆成功！\n获得流量：{today_data}GB\n{messaage1}"

        elif duihuan_flag == 'False':
            message = f"{email}登陆成功！\n获得流量：{today_data}GB"

        send_push_notification(message, pushplus_token)
    else:
        print(f"{email}登录失败，请检查账号密码是否正确")
