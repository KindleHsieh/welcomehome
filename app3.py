# -*- coding: utf-8 -*-
# author: Kindle Hsieh time: 2019/12/24

from linebot import LineBotApi, WebhookHandler
# 引用無效簽章錯誤
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    ImagemapSendMessage, TextSendMessage, ImageSendMessage,
    LocationSendMessage, FlexSendMessage, VideoSendMessage
)
from linebot.models import (
    FollowEvent, MessageEvent, TextMessage, PostbackEvent)
from linebot.models.template import *
import json
import csv
import random
from flask import request, Flask, abort
from urllib.parse import parse_qs
from datetime import datetime, timedelta

import os

"""
    Intialization.
    Basic setting...
    Contain LinBotApi and Flask.
"""
SecretFileContentJson = json.load(open('./line_secret_key', 'r', encoding='utf8'))
line_bot_api = LineBotApi(SecretFileContentJson.get('channel_access_token'))
handler = WebhookHandler(SecretFileContentJson.get('secret_key'))

# Flask.
# 設定Server啟用細節
app = Flask(__name__, static_url_path="/素材", static_folder="./素材/")


# 啟動server對外接口，使Line能丟消息進來。
@app.route("/", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


'''

消息判斷器

讀取指定的json檔案後，把所包含的數個類型的Message，轉換成不同格式的SendMessage

讀取檔案，
把內容轉換成json
將json轉換成消息
放回array中，並把array傳出。

'''


def detect_json_array_to_new_message_array(fileName):
    # 開啟檔案，轉成json
    with open(fileName) as f:
        jsonArray = json.load(f)

    # 解析json
    returnArray = []
    for jsonObject in jsonArray:

        # 讀取其用來判斷的元件
        message_type = jsonObject.get('type')

        # 轉換
        if message_type == 'text':
            returnArray.append(TextSendMessage.new_from_json_dict(jsonObject))
        elif message_type == 'imagemap':
            returnArray.append(ImagemapSendMessage.new_from_json_dict(jsonObject))
        elif message_type == 'template':
            returnArray.append(TemplateSendMessage.new_from_json_dict(jsonObject))
        elif message_type == 'image':
            returnArray.append(ImageSendMessage.new_from_json_dict(jsonObject))
        elif message_type == 'sticker':
            returnArray.append(StickerSendMessage.new_from_json_dict(jsonObject))
        elif message_type == 'audio':
            returnArray.append(AudioSendMessage.new_from_json_dict(jsonObject))
        elif message_type == 'location':
            returnArray.append(LocationSendMessage.new_from_json_dict(jsonObject))
        elif message_type == 'flex':
            returnArray.append(FlexSendMessage.new_from_json_dict(jsonObject))
        elif message_type == 'video':
            returnArray.append(VideoSendMessage.new_from_json_dict(jsonObject))

            # 回傳
    return returnArray


'''

handler處理關注消息

用戶關注時，讀取 素材 -> 關注 -> follow.json

將其轉換成可寄發的消息，傳回給Line

'''


@handler.add(FollowEvent)
def process_follow_event(event):
    # get user profile.
    user_profile = line_bot_api.get_profile(event.source.user_id)
    user_id = event.source.user_id
    print('user_id:', user_id)

    # Json 管理users資料. 使用user_id當作keys.
    # load json
    try:
        # 使用r+可以幫我判斷檔案是否存在，並且保證我可以讀取到json格式資料。
        f = open('users.json', 'r+', encoding='utf-8')
    except FileNotFoundError:
        f = open('users.json', 'w', encoding='utf-8')
        user = {}
    else:
        user = json.load(f)
    u = vars(user_profile)
    user_id = u.pop("user_id")
    # 判斷用戶是否已經登記在此系統了。
    # 因為不想要覆蓋已經存在的資料，可𠹌已經記錄過其他資訊，但被重新關注刷新。
    if user_id not in user.keys():
        user[user_id] = u

    # 新朋友關注。
    # if ('age' not in user[user_id].keys()) | ('team' not in user[user_id].keys()):
    if 'have' not in user[user_id].keys():
        # 新朋友歡迎詞及表單。
        # Load and transfer follow information.
        json_path = './素材/關注/new_reply.json'
        result_message_array = detect_json_array_to_new_message_array(json_path)

        # 新朋友 rich menu.
        link_rich_menu_id = open('素材/rich_menu/new_friend/' + 'rich_menu_id', 'r', encoding='utf-8').read()
        line_bot_api.link_rich_menu_to_user(user_id, link_rich_menu_id)

    # 舊朋友關注。
    else:
        # 舊朋友歡迎詞及表單。
        # Load and transfer follow information.
        json_path = './素材/關注/old_reply.json'
        result_message_array = detect_json_array_to_new_message_array(json_path)

        # 小羊 rich menu.
        if 'leader' not in user[user_id].keys():
            link_rich_menu_id = open('素材/rich_menu/old_friend/' + 'rich_menu_id', 'r', encoding='utf-8').read()
            line_bot_api.link_rich_menu_to_user(user_id, link_rich_menu_id)
        elif user[user_id]['leader'] == 0:
            link_rich_menu_id = open('素材/rich_menu/old_friend/' + 'rich_menu_id', 'r', encoding='utf-8').read()
            line_bot_api.link_rich_menu_to_user(user_id, link_rich_menu_id)
        # 小組長 rich menu.
        else:
            link_rich_menu_id = open('素材/rich_menu/leader/' + 'rich_menu_id', 'r', encoding='utf-8').read()
            line_bot_api.link_rich_menu_to_user(user_id, link_rich_menu_id)

    # Load and transfer follow information.
    result_message_array = detect_json_array_to_new_message_array(json_path)

    line_bot_api.reply_message(
        event.reply_token,
        result_message_array)

    # Save file in the end.
    f.seek(0, 0)
    json.dump(user, f)


'''

handler處理文字消息

收到用戶回應的文字消息，
按文字消息內容，往素材資料夾中，找尋以該內容命名的資料夾，讀取裡面的reply.json

轉譯回應消息(json)後，將消息回傳給用戶

'''


# 文字消息處理
@handler.add(MessageEvent, message=TextMessage)
def process_text_message(event):
    # 如果文字帶有'+--<3'表示開始輸入「密碼」。
    if '+-<3' == event.message.text[:4]:
        user_id = event.source.user_id
        users_file = open('users.json', 'r+', encoding='utf-8')
        user = json.load(users_file)
        user_age = user[user_id]['age']
        user_team = user[user_id]['team']

        # 根據age and team代號查詢密碼。
        rows = csv.reader(open('age_team.csv', 'r', encoding='utf8', newline=''), delimiter=',')
        for r in rows:
            # r[0]=age, r[1]=team.
            if (r[0] == user_age) & (r[1] == user_team):
                # 回應密碼正確-消息。
                if r[2] == event.message.text[4:]:
                    # json_path = "素材/password" + event.message.text + "/right_reply.json"
                    json_path = {"type": "text", "text": "登登！恭喜你輸入正確！下方圖文選單有變化喔，快去看看有哪些功能吧！"}
                    result_message_array = TextSendMessage.new_from_json_dict(json_path)
                    user[user_id]['have'] = 1
                    users_file.seek(0, 0)
                    json.dump(user, users_file)
                    users_file.truncate()

                    # 小羊 rich menu.
                    link_rich_menu_id = open('素材/rich_menu/old_friend/' + 'rich_menu_id', 'r',
                                             encoding='utf-8').read()
                    line_bot_api.link_rich_menu_to_user(user_id, link_rich_menu_id)
                # 回應密碼不正確-消息。
                else:
                    # json_path = "素材/password" + event.message.text + "/bad_reply.json"
                    json_path = {"type": "text", "text": "哋哋～你輸入的密碼不正確唷，請小組長幫幫你吧！"}
                    result_message_array = detect_json_array_to_new_message_array(json_path)
            else:
                print('This team is not exist.')
    elif '[+-<3]' == event.message.text[:6]:
        # 這邊有偷懶，僅檢查是不是有leader且為0才能動。沒有檢查哪個小家等資訊
        user_id = event.source.user_id
        users_file = open('users.json', 'r+', encoding='utf-8')
        user = json.load(users_file)
        if 'have' in user[user_id].keys():
            if 'leader' in user[user_id].keys():
                # 輸入密碼正確。
                if (user[user_id]['leader'] == '0') and ("是我的責任" == event.message.text[6:]):
                    user[user_id]['leader'] = 1
                    json_path = {"type": "text", "text": "登愣登愣～恭喜往前成為帶領羊群的小組長！"}
                    result_message_array = TextSendMessage.new_from_json_dict(json_path)
                    # 小組長選單。
                    link_rich_menu_id = open('素材/rich_menu/leader/' + 'rich_menu_id', 'r', encoding='utf-8').read()
                    line_bot_api.link_rich_menu_to_user(user_id, link_rich_menu_id)
            users_file.seek(0, 0)
            json.dump(user, users_file)
            users_file.truncate()

    # pray 指令，會直接更新(覆蓋)我們的代禱事項。
    elif 'pray' == event.message.text[:4]:
        # 有確定小組的才可以使用此功能。
        # 查詢這個人是誰。
        # 這個人是屬於哪個小家。
        # 開啟那個小家的資料做加減查詢。
        user_id = event.source.user_id
        users_file = open('users.json', 'r+', encoding='utf-8')
        user = json.load(users_file)
        if 'have' in user[user_id].keys():
            user_age = user[user_id]['age']
            user_team = user[user_id]['team']
            user_name = user[user_id]['display_name']
            try:
                f = open(f'./素材/pray_for_me/{user_age}{user_team}.json', 'r+', encoding='utf-8')

                pray = json.load(f)

            except FileNotFoundError:
                f = open(f'./素材/pray_for_me/{user_age}{user_team}.json', 'w', encoding='utf-8')
                pray = {}

            if user_name not in pray.keys():
                pray[user_name] = {}
            # 根據現在為第幾週來更新代禱內容存放位置。
            pray[user_name][datetime.now().isocalendar()[1]] = event.message.text[4:]
            f.seek(0, 0)
            json.dump(pray, f)
            f.truncate()
            json_path = {"type": "text", "text": "更新代禱內容完成。"}
            result_message_array = TextSendMessage.new_from_json_dict(json_path)

    # pray_ 指令，會直接新增我們的代禱事項。
    elif '_pray' == event.message.text[:5]:
        user_id = event.source.user_id
        users_file = open('users.json', 'r+', encoding='utf-8')
        user = json.load(users_file)
        if 'have' in user[user_id].keys():
            user_age = user[user_id]['age']
            user_team = user[user_id]['team']
            user_name = user[user_id]['display_name']
            try:
                f = open(f'./素材/pray_for_me/{user_age}{user_team}.json', 'r+', encoding='utf-8')
                pray = json.load(f)
            except FileNotFoundError:
                f = open(f'./素材/pray_for_me/{user_age}{user_team}.json', 'w', encoding='utf-8')
                pray = {}

            if user_name not in pray.keys():
                pray[user_name] = {}
            # 根據現在為第幾週來新增代禱內容存放位置。
            # 原資料後方加上'、'再繼續輸入內容。。
            try:
                s = pray[user_name][str(datetime.now().isocalendar()[1])]
                pray[user_name][str(datetime.now().isocalendar()[1])] = s + '、' + event.message.text[5:]
            except KeyError:
                pray[user_name][str(datetime.now().isocalendar()[1])] = event.message.text[5:]

            f.seek(0, 0)
            json.dump(pray, f)
            f.truncate()
            json_path = {"type": "text", "text": "新增代禱內容完成。"}
            result_message_array = TextSendMessage.new_from_json_dict(json_path)

    # 查詢小組內成員代禱事項。
    # 資料顯示方式為：
    # 人名：人名＋：＋換行。
    # 內容：空兩格＋代禱內容＋換行。
    elif'代禱' == event.message.text[:2]:
        user_id = event.source.user_id
        users_file = open('users.json', 'r+', encoding='utf-8')
        user = json.load(users_file)
        if 'have' in user[user_id].keys():
            user_age = user[user_id]['age']
            user_team = user[user_id]['team']
            try:
                with open(f'./素材/pray_for_me/{user_age}{user_team}.json', 'r', encoding='utf-8') as f:
                    pray = json.load(f)
                    show = ''
                    for person in pray:
                        try:
                            text = pray[person][str(datetime.now().isocalendar()[1])]
                        except KeyError:
                            continue
                        text = text.split('、')

                        show += person + ':\n'
                        for t in text:
                            show += '  ' + t + '\n'
                    json_path = {"type": "text", "text": show}
                    result_message_array = TextSendMessage.new_from_json_dict(json_path)
            except FileNotFoundError:
                json_path = {"type": "text", "text": "小組還沒有成員有代禱過喔！"}
                result_message_array = TextSendMessage.new_from_json_dict(json_path)

    elif '聽聽上帝的聲音' == event.message.text:
        ff = csv.reader(open('素材/聽聽上帝的聲音/gods_voice.csv', 'r', encoding='utf-8', newline=''), delimiter=',')
        ran = random.randint(1, 21)
        # [0]: No. [1]:content
        for i, f in enumerate(ff):
            if i == ran:
                json_path = {"type": "text", "text": f[1]}
                result_message_array = TextSendMessage.new_from_json_dict(json_path)

    else:
        # 讀取本地檔案，並轉譯成消息
        json_path = "素材/" + event.message.text + "/reply.json"
        result_message_array = detect_json_array_to_new_message_array(json_path)

    # 發送
    line_bot_api.reply_message(
        event.reply_token,
        result_message_array
    )


'''
handler處理Postback Event

解析postback的data，並按照data欄位判斷處理
'''

'''
現有三個欄位
menu, folder, tag

若folder欄位有值，則
    讀取其reply.json，轉譯成消息，並發送

若menu欄位有值，則
    讀取其rich_menu_id，並取得用戶id，將用戶與選單綁定
    讀取其reply.json，轉譯成消息，並發送

先處理有「回傳」的消息，在處理標籤，除非這個標籤影響回傳的消息內容。
'''


@handler.add(PostbackEvent)
def process_postback_event(event):
    user_id = event.source.user_id
    query_dict = parse_qs(event.postback.data)
    # print(event.postback.params['date'])

    #  回傳型消息。

    if 'func' in query_dict:
        if '每日靈糧' == query_dict['func'][0]:

            date_now = datetime.now().date()
            date_future = date_now + timedelta(days=30)
            date_pass = date_now - timedelta(days=365)
            try:
                query_date = event.postback.params['date']
            except:
                query_date = str(date_now)
            json_path = '素材/func/每日靈糧/' + query_date + '/reply.json'
            result_message_array = detect_json_array_to_new_message_array(json_path)
            result_message_array.append(
                TemplateSendMessage.new_from_json_dict({
                "type": "template",
                "altText": "this is a buttons template",
                "template": {
                    "type": "buttons",
                    "actions": [
                        {
                            "type": "datetimepicker",
                            "label": "選取日期",
                            "data": "func=每日靈糧",
                            "mode": "date",
                            "initial": str(date_now),
                            "max": str(date_future),
                            "min": str(date_pass)
                        }
                    ],
                    "text": "查詢每日靈糧嗎？"
                }
            }))
        else:
            json_path = '素材/func/' + query_dict['func'][0] + '/reply.json'
            result_message_array = detect_json_array_to_new_message_array(json_path)

        line_bot_api.reply_message(
            event.reply_token,
            result_message_array)

    elif 'menu' in query_dict:
        json_path = '素材/rich_menu/' + query_dict['menu'][0] + '/reply.json'
        result_message_array = detect_json_array_to_new_message_array(json_path)

        line_bot_api.reply_message(
            event.reply_token,
            result_message_array)

        link_rich_menu_id = open('素材/rich_menu/' + query_dict['menu'][0] + 'rich_menu_id', 'r', encoding='utf-8').read()
        line_bot_api.link_rich_menu_to_user(user_id, link_rich_menu_id)

    elif 'identity' in query_dict:
        user_file = open('users.json', 'r+', encoding='utf=-8')
        user = json.load(user_file)
        if 'have' in user[user_id].keys():
            pass
            if user[user_id]['have'] == "1":
                pass
        else:
            json_path = '素材/func/' + query_dict['identity'][0] + '/reply.json'
            result_message_array = detect_json_array_to_new_message_array(json_path)

            line_bot_api.reply_message(
                event.reply_token,
                result_message_array)

    elif 'quit' in query_dict:
        user_file = open('users.json', 'r+', encoding='utf=-8')
        user = json.load(user_file)
        # 小羊 rich menu.
        if 'leader' not in user[user_id].keys():
            link_rich_menu_id = open('素材/rich_menu/old_friend/' + 'rich_menu_id', 'r', encoding='utf-8').read()
            line_bot_api.link_rich_menu_to_user(user_id, link_rich_menu_id)
        elif user[user_id]['leader'] == 0:
            link_rich_menu_id = open('素材/rich_menu/old_friend/' + 'rich_menu_id', 'r', encoding='utf-8').read()
            line_bot_api.link_rich_menu_to_user(user_id, link_rich_menu_id)
        # 小組長 rich menu.
        else:
            link_rich_menu_id = open('素材/rich_menu/leader/' + 'rich_menu_id', 'r', encoding='utf-8').read()
            line_bot_api.link_rich_menu_to_user(user_id, link_rich_menu_id)

    # 標籤。
    # 跟「標籤」有關的資訊通常都需要load個人資料，先load可以避免後面要一直重複load。
    user_file = open('users.json', 'r+', encoding='utf=-8')
    user = json.load(user_file)
    if 'age' in query_dict:
        # 有have標籤(已經正式進入小組)，就不能再更改。
        # 沒有have標籤，就能換小組。
        if 'have' not in user[user_id].keys():
            user[user_id]['age'] = query_dict['age'][0]
        # age固定了，回應已經有小組囉，不能再更改資訊。
        else:
            json_path = {"type": "text", "text": "你已經有小組囉！"}
            result_message_array = TextSendMessage.new_from_json_dict(json_path)

            line_bot_api.reply_message(
                event.reply_token,
                result_message_array)

    if 'team' in query_dict:
        # 有have標籤(已經正式進入小組)，就不能再更改。
        # 沒有have標籤，就能換小組。
        if 'have' not in user[user_id].keys():
            user[user_id]['team'] = query_dict['team'][0]
        # age固定了，回應已經有小組囉，不能再更改資訊。
        else:
            json_path = {"type": "text", "text": "你已經有小組囉！"}
            result_message_array = TextSendMessage.new_from_json_dict(json_path)

            line_bot_api.reply_message(
                event.reply_token,
                result_message_array)

    if 'leader' in query_dict:
        # 要先有小組，才能成為小組長。
        user[user_id]['leader'] = query_dict['leader'][0]

    for k, v in user.items():
        print(k, ':', v)
    user_file.seek(0, 0)
    json.dump(user, user_file)
    user_file.truncate()

'''

Application 運行（開發版）

'''
if __name__ == "__main__":
    app.run(host='0.0.0.0')

# In[ ]:


'''

Application 運行（heroku版）

'''

# import os
# if __name__ == "__main__":
#     app.run(host='0.0.0.0',port=os.environ['PORT'])