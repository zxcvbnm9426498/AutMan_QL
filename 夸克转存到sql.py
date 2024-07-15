import requests,json,time,os
import urllib.parse
import concurrent.futures
import pymysql
from threading import local
import re

# 定义一个清理标题的函数
def clean_title(title):
    # 使用正则表达式匹配标题开头的数字和点
    cleaned_title = re.sub(r'^\d+\.', '', title).strip()
    return cleaned_title

# 数据库配置
username = 'duanju'
password = 'NjLeSXfeydZbeFWT'  # 请确保密码处理得当，避免代码泄露
hostname = '8.130.122.112'
port = 3306  # 端口是整数，不应该是字符串
database_name = 'duanju'
table_name = 'duanju_short_film'
connection = pymysql.connect(host=hostname,
                             user=username,
                             password=password,
                             port=port,
                             database=database_name,
                             cursorclass=pymysql.cursors.DictCursor)

threadlocal = local()

def get_cursor():
    if not hasattr(threadlocal, "cursor"):
        # 创建新的数据库连接和游标，每个线程一个
        connection = pymysql.connect(host=hostname,
                                     user=username,
                                     password=password,
                                     port=port,
                                     database=database_name,
                                     cursorclass=pymysql.cursors.DictCursor)
        cursor = connection.cursor()
        threadlocal.connection = connection
        threadlocal.cursor = cursor
    return threadlocal.cursor

# 定义插入功能，重用已打开的数据库连接
def insert_link_to_database(title, link):
    cursor = get_cursor()
    insert_query = f"INSERT INTO {table_name} (Title, Link) VALUES (%s, %s)"
    cursor.execute(insert_query, (title, link))
    threadlocal.connection.commit()

# 定义转存函数，这里将需要并行执行的代码放入此函数
def process_link(session, headers, url_list_item, to_pdir_fid):
    temp = url_list_item.split(" >>>> ")
    raw_title = temp[0]  # 获取原始标题
    title = clean_title(raw_title)  # 清理标题
    link = temp[1]  # 获取链接
    print(f"开始处理链接，标题为【{title}】，链接为【{link}】")

    # 插入到数据库中的操作，确保调用了线程安全的版本
    insert_link_to_database(title, link)
    
    pwd_id = temp[1].split("/")[-1]
    t = str(int(time.time() * 1000))
    
    # 下面的URL3 URL4 URL5 变量必须根据实际情况进行调整
    url3 = f'https://drive-pc.quark.cn/1/clouddrive/share/sharepage/token?pr=ucpro&fr=pc&uc_param_str=&__dt=959&__t={t}'
    body = {"pwd_id": pwd_id, "passcode": ""}
    payload = json.dumps(body)
    response3 = session.post(url=url3, headers=headers, data=payload)
    ccc = json.loads(response3.text)
    stoken = ccc['data']['stoken']
    stoken_parse = urllib.parse.quote(stoken)
    t = str(int(time.time() * 1000))
    
    url4 = f'https://drive-pc.quark.cn/1/clouddrive/share/sharepage/detail?pr=ucpro&fr=pc&uc_param_str=&pwd_id={pwd_id}&stoken={stoken_parse}&pdir_fid=0&force=0&_page=1&_size=50&_fetch_banner=1&_fetch_share=1&_fetch_total=1&_sort=file_type:asc,updated_at:desc&__dt=1371&__t={t}'
    response4 = session.get(url=url4, headers=headers)
    ccc_4 = json.loads(response4.text)
    fid_list = ccc_4['data']['list'][0]['fid']
    fid_token_list = ccc_4['data']['list'][0]['share_fid_token']
    t = str(int(time.time() * 1000))
    
    url5 = f'https://drive-pc.quark.cn/1/clouddrive/share/sharepage/save?pr=ucpro&fr=pc&uc_param_str=&__dt=7093&__t={t}'
    body = {"fid_list": [fid_list], "fid_token_list": [fid_token_list], "to_pdir_fid": to_pdir_fid, "pwd_id": pwd_id, "stoken": stoken, "pdir_fid": "0", "scene": "link"}
    payload = json.dumps(body)
    response5 = session.post(url=url5, headers=headers, data=payload)

    # 处理转存响应结果
    try:
        response_data = json.loads(response5.text)
        if 'task_id' in response_data['data']:
            print(f"【{title}】转存成功~")
        else:
            if 'errmsg' in response_data:
                print(f"【{title}】转存失败，原因：{response_data['errmsg']}")
            else:
                print(f"【{title}】转存失败，未知原因。")
    except Exception as e:
        print(f"处理链接【{title}】时出错。错误信息：{str(e)}")

    # 最后返回处理结果，方便调用者了解每个链接处理情况
    return f"处理完毕【{title}】。"

# 主函数中使用多线程部分，现在应该移到 if __name__ == "__main__": 保护块中
if __name__ == "__main__":
    ck = input("请输入CK：")
    t = str(int(time.time()*1000))
    url = f'https://pan.quark.cn/account/info?fr=pc&platform=pc&__dt=647&__t={t}'
    headers = {
                "accept": "application/json, text/plain, */*",
                "accept-encoding": "gzip, deflate, br",
                "accept-language": "zh-CN,zh;q=0.9,yo;q=0.8",
                "cookie": ck,
                "dnt": "1",
                "origin": "https://pan.quark.cn",
                "referer": "https://pan.quark.cn/",
                "sec-ch-ua": '''"Chromium";v="21", " Not;A Brand";v="99"''',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "Windows",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "user-agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"}
    response = requests.get(url=url,headers=headers)
    try:
        aaa = json.loads(response.text)
        nickname = aaa['data']['nickname']
        if nickname != None:
            is_login = 1
            print(f"获取到昵称：【{nickname}】")
    except Exception:
        print(response.text)
        is_login = 0
        print(f"未获取到用户信息，请重新抓取CK")
    time.sleep(1)
    if is_login == 1:
        print(f"请先在网盘根目录中新建文件夹，下方需选择保存的文件夹")
        url = f"https://drive-pc.quark.cn/1/clouddrive/file/sort?pr=ucpro&fr=pc&uc_param_str=&pdir_fid=0&_page=1&_size=50&_fetch_total=1&_fetch_sub_dirs=0&_sort=file_type:asc,file_name:asc"
        response = requests.get(url=url, headers=headers)
        try:
            aaa = json.loads(response.text)
            total = aaa['metadata']['_total']
            print(f'根目录找到{total}个文件夹\n——————————————')
            i = 0
            fid_temp = []
            for list in aaa['data']['list']:
                file_name = list['file_name']
                fid = list['fid']
                fid_temp.append(fid)
                print(i+1,file_name)
                i = i + 1
        except Exception:
            print(f"出错了，请确认根目录是否有文件夹")

        a = int(input('\n请输入序号选择保存的文件夹，回车确认\n'))
        # 选择文件夹
        to_pdir_fid = fid_temp[a-1]
        print(f"选择了第{a}个文件夹，fid 为 {to_pdir_fid}，下面开始转存。")

        # 读取URL列表
        with open('夸克网盘一键转存链接.txt', 'r+', encoding="UTF-8") as f:
            kkk = f.read()
        url_list = kkk.strip().split('\n')
        print(f"共有{len(url_list)}个链接")

        # 使用线程池
        with requests.Session() as session, concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_link, session, headers, url, to_pdir_fid) for url in url_list]
            
            # 等待线程池中的任务完成
            for future in concurrent.futures.as_completed(futures):
                print(future.result())

            # 等待所有线程完成工作后关闭线程局部的数据库连接
            if hasattr(threadlocal, "connection"):
                threadlocal.connection.close()