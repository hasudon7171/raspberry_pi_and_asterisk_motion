
# coding:utf-8

import sys
import os
import shutil
import requests
import pprint
import urllib
import urllib2
import json
import ConfigParser

TOKEN                 = '<トークン>'
CHANNEL               = '<チャンネルID>'
CALLFILE_DIR          = '<自動発信ファイルディレクトリ>'
CALLFILE_NAME         = 'auto_call.call'    # 自動発信ファイル名
OUTGOING_DIR          = '/var/spool/asterisk/outgoing/'
CALL_NOTIFY_START_STR = 'call';       # 電話通知ON判定文字列
CALL_NOTIFY_END_STR   = 'nocall';     # 電話通知OFF判定文字列
INIFILE_PATH          = '<設定ファイルPATH>'
SECTION               = 'motion notify'

# slack API : channels.info
# 参考：https://api.slack.com/methods/channels.info
####
def get_channel_info():

    url = "https://slack.com/api/channels.info"

    params = {'token'  : TOKEN,
              'channel': CHANNEL,
    }

    params = urllib.urlencode(params)

    req    = urllib2.Request(url)
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')

    req.add_data(params)

    res     = urllib2.urlopen(req)
    body    = res.read()
    result  = json.loads(body)

    return result

# 電話通知ON/OFF設定
# slack_last_text : slackから受信した最新の投稿のテキスト部分
####
def set_call_notify(slack_last_text):

    config = ConfigParser.SafeConfigParser()

    if not config.has_section(SECTION):
        config.add_section(SECTION)

    # 設定ファイルの内容取得
    try :
        config.read(INIFILE_PATH)
        ini_set = config.get(SECTION,'enable')
    except Exception as e:
        ini_set = 'FALSE'

    if slack_last_text == CALL_NOTIFY_START_STR:
        config.set(SECTION, 'enable', 'TRUE')
        ini_set = 'TRUE'

    elif slack_last_text == CALL_NOTIFY_END_STR:
        config.set(SECTION, 'enable', 'FALSE')
        ini_set = 'FALSE'
    else:
        config.set(SECTION, 'enable', ini_set)

    config.write(open(INIFILE_PATH, 'w'))

    return ini_set

# 自動発信ファイル生成 -> outgoing
####
def outgoing_call():

    file_str = '''#
Channel: SIP/<通知先電話番号>@<外線発信するセクション名>
MaxRetries: 0
RetryTime: 60
WaitTime: 30
Context: default
Extension: <extension.confに沿ったEXTEN>
Priority: 1'''

    file = open(CALLFILE_DIR +CALLFILE_NAME, "w")
    file.writelines(file_str);
    file.close()

    os.chmod(CALLFILE_DIR + CALLFILE_NAME, 0755)
    shutil.move(CALLFILE_DIR + CALLFILE_NAME, OUTGOING_DIR)

# slack API : files.upload
# 参考：https://api.slack.com/methods/files.upload
####
def upload_file(file_path, channel):

    with open(file_path,'rb') as f:
        param = {'token':TOKEN, 'channels':CHANNEL,}
        r = requests.post("https://slack.com/api/files.upload", params=param,files={'file':f})


if __name__ == "__main__":

    channnels_info = get_channel_info()

    is_call = set_call_notify(channnels_info['channel']['latest']['text'])

    print is_call

    if is_call == 'TRUE':
        outgoing_call()

    arg     = sys.argv
    file_path = arg[1]

    upload_file(file_path, CHANNEL)

