# -*- coding: utf-8 -*-
# author: Kindle Hsieh time: 2019/12/19

'''
迴圈讀取本地列表，
    上傳設定檔，取得id，並將id寫入檔案中，而後上傳圖片
'''

import json
from linebot import LineBotApi

SecretFileContentJson = json.load(open("./line_secret_key", "r", encoding='utf-8'))
line_bot_api = LineBotApi(SecretFileContentJson['channel_access_token'])




############ FUNCTION.################
'''
設定新的rich_menu。

讀取menu的json檔，上傳資料後取得menu_id，
'''
rich_menu_array = ['leader', 'new_friend', 'old_friend']

from linebot.models import RichMenu
for rich_menu in rich_menu_array:
    # Create rich menu and get Menu_ID by Json.
    menu_id = ''
    with open('素材/rich_menu/'+rich_menu+'/rich_menu.json', 'r') as f:
        menu_id = line_bot_api.create_rich_menu(RichMenu.new_from_json_dict(json.load(f)))
    print("-設定檔上傳結果")
    print(menu_id)

    # Write menu_id in local file.
    with open("素材/rich_menu/" + rich_menu + "/rich_menu_id", "w", encoding='utf8') as f:
        f.write(menu_id)

    # Upload images. [jpg.]
    with open("素材/rich_menu/"+rich_menu+'/rich_menu.jpg', 'rb') as f:
        set_image_response = line_bot_api.set_rich_menu_image(menu_id, 'image/jpeg', f)
    print('-圖片上傳結果:', set_image_response)


'''

查詢「所建立的官方網站」內擁有的richmenu.

'''
menu_id_list = line_bot_api.get_rich_menu_list()
for li in menu_id_list:
    print(li)


# '''
# 移除帳號內的richmenu
# Line帳號內最多擁有1000個rich menu.
#
# '''
# # Set rich menu 'name' which you want to delete.
# rich_menu_delete_array = ["rich_menu_0"]
# for rich_menu_delete in rich_menu_delete_array:
#     # Load the menu_id and delete from both local and LINE.
#     with open(' ', 'w+', encoding='utf-8') as f:
#         # Delete from LINE.
#         line_bot_api.delete_rich_menu(f.read())
#         f.write('')


# '''
#
# 綁定個人用戶與rich menu.
#
# '''
# user_id = ''
# menu_id = ''
# line_bot_api.link_rich_menu_to_user(user_id, menu_id)




# '''
#
# 解除用戶綁定
#
# '''
# user_id = ''
# line_bot_api.unlink_rich_menu_from_user(user_id)


