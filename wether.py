#[title: 天气推送]
#[language: python]
#[service: 10086]
#[disable: false]
#[admin: false]
#[rule: ^天气$]
#[cron: 45 6 * * *]
#[priority: 0]
#[platform: all] 适用的平台
#[open_source: true]是否开源
#[version: 1.0.0]
#[public: false] 是否发布？
#[price: 0.01] 
#[description: 定时推送天气信息，同时也支持定时推送]
import requests
import json
import middleware

senderID = middleware.getSenderID()
sender = middleware.Sender(senderID)
user=sender.getUserID()
content = sender.getMessage()

#获取天气
def print_weather_info(api_key, city_id):
    '''
    "小店区"=>"101100107"
    "通辽"=>"101080501"
    "科尔沁左翼后旗"=>"101080504"
    "原平"=>"101101015"
    "太原"=>"101100101"
    :param api_key: api_key地址：www.tianapi.com
    :param city_id:可以是城市天气ID、行政代码、城市名称、IP地址
    :return:天气的具体数据
    '''
    url = f"https://apis.tianapi.com/tianqi/index?key={api_key}&city={city_id}&type=1"
    try:
        response = requests.get(url)
        data = response.json()
        result = data.get('result')
        if result:
            city = result.get('area')                       # 城市
            temperature = result.get('real')                # 实时温度
            weather = result.get('weather')                 # 天气
            tips = result.get('tips')                       # 温馨提示
            highest = result.get('highest')                 # 最高温度
            lowest = result.get('lowest')                   # 最低温度
            wind = result.get('wind')                       # 风向
            pcpn = result.get('pcpn')                       # 降水量
            quality = result.get('quality')                 # 空气质量
            uv_index = result.get('uv_index')               # 紫外线指数
            alarm_list = result.get('alarmlist')            # 预警信息
            if alarm_list:                                  # 预警内容
                level = alarm_list[0].get('level')          # 预警级别
                alarm_type = alarm_list[0].get('type')      # 预警类型
                time = alarm_list[0].get('time')            # 预警时间
                content = alarm_list[0].get('content')      # 预警内容
            else:
                level = alarm_type = time = content = None
        else:
            print("API响应中未找到天气数据。")
    except requests.RequestException as e:
        print(f"获取天气数据失败：{e}")
    return city,temperature,weather,tips,highest,lowest,wind,pcpn,quality,uv_index,level,alarm_type,time,content
#获取日期
def get_riqi():
    import datetime
    def get_weekday(date):
        weekdays = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
        weekday = date.weekday()
        # 获取当前日期
        current_date = datetime.date.today()
        # 格式化日期为"xxxx年xx月xx日"的格式
        formatted_date = current_date.strftime("%Y年%m月%d日")
        return formatted_date,weekdays[weekday]
    # 获取当前日期
    current_date = datetime.date.today()
    # 获取当前日期对应的星期
    formatted_date,weekday= get_weekday(current_date)
    new_variable = formatted_date + ", " + weekday
    return new_variable


#主程序
def main():
    city,temperature,weather,tips,highest,lowest,wind,pcpn,quality,uv_index,level,alarm_type,time,content = print_weather_info('76c6cd8b0cf5a94851b4dd2fed735b1e', '101100107')
    message = "早上好，今天又是美好的一天，今天的天气如下：\n"
    message += f"{city}的天气信息如下：\n"
    message += f"日期：{get_riqi()}\n"
    message += f"天气：{weather}\n"
    message += f"温度：{temperature}，最高温度：{highest}，最低温度：{lowest}\n"
    message += f"风向：{wind}\n"
    message += f"降水量：{pcpn}\n"
    message += f"空气质量：{quality}\n"
    message += f"紫外线指数：{uv_index}\n"
    message += f"温馨提示：{tips}"
    if level:
        message += f"预警：{level}级{alarm_type}，{time}，{content}\n"
    else:
        #message += "当前无预警信息。"
        None
    
    #print(message)
    return message

if __name__ == '__main__':
    if content == "天气":
        message = main()
        sender.reply(message)
    else:
        if sender.getImtype() == "fake":
            message = main()
            middleware.notifyMasters(message)
        