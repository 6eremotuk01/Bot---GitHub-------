# Укажите персональный токен JetBrain Space
API_TOKEN = ""
ORGANIZATION_NAME = ""  # Укажите наименование организации
CHANNEL_NAME = "it_github_bot"  # Укажите имя канала

import requests
import json
from bottle import route, run, post, request

CHANNEL_ID = ''
REQUEST_HEADERS = {
    'Authorization': "Bearer {0}".format(API_TOKEN),
    'Accept': 'application/json',
}


def getChannelsInfo(nameOfChannel=""):
    global ORGANIZATION_NAME
    global REQUEST_HEADERS

    query = "https://{0}.jetbrains.space/api/http/chats/channels/all-channels?query={1}".format(
        ORGANIZATION_NAME, nameOfChannel)
    print("Получение информации о каналах/канале...")

    response = requests.get(query, headers=REQUEST_HEADERS)
    print("Запрос успешно отправлен. Ответ сервера:\n {0} \n\n".format(
        json.dumps(response.text, sort_keys=True, indent=4)))

    return json.loads(response.text)


def sendMessage(channelId, message):
    global ORGANIZATION_NAME
    global REQUEST_HEADERS

    query = "https://{0}.jetbrains.space/api/http/chats/channels/{1}/messages".format(
        ORGANIZATION_NAME, channelId)

    print("Отправка сообщения:\n{0}".format(message))
    dataToSend = {"text": message}
    response = requests.post(query, headers=REQUEST_HEADERS, json=dataToSend)
    print("Cообщение успешно отправлено . Ответ сервера:\n {0}\n\n".format(
        json.dumps(response.text, sort_keys=True, indent=4)))

    return json.loads(response.text)


@post('/post')
def doPost():
    print("Произолшло событие GitHub: \n {0} \n\n".format(
        json.dumps(request.json, sort_keys=True, indent=4)))

    global CHANNEL_ID

    ### Поля
    # 0 — Имя пользователя
    # 1 — Полное имя
    # 2 — Количество комитов
    # 3 — Буква s, которая отображает мн. число
    # 4 — Имя репозитория
    ### Cссылки
    # 5 — Ссылка на пользователя
    # 6 — Ссылка на изменения
    # 7 — Ссылка на репозиторий
    headerFormat = ">**[{0} ({1})]({5})**\n>[{2} new commit{3}]({6}) pushed to [{4}]({7})"

    ### Поля
    # 0 — Первые 7 символов id коммита
    # 1 — Заголовок коммита
    commitFormat = "\n>\xa0\xa0\xa0[{0}]({2}) — {1}"

    # Заполнение полей
    message = ''
    jsonedData = json.load(request.body)
    username = jsonedData['head_commit']['author']['username']
    fullname = jsonedData['head_commit']['author']['name']
    commitsCount = len(jsonedData['commits'])
    sLetter = "" if commitsCount != 1 else 's'
    repositoryName = jsonedData['repository']['name']
    commits = jsonedData['commits']

    userLink = jsonedData["sender"]["html_url"]
    commitsCountLink = jsonedData["compare"]
    repositoryLink = jsonedData["repository"]["html_url"]

    # Формирование сообщения
    message += headerFormat.format(username, fullname, commitsCount, sLetter,
                                   repositoryName, userLink, commitsCountLink,
                                   repositoryLink)
    for item in commits:
        message += commitFormat.format(item['id'][0:6], item['message'],
                                       item["url"])

    sendMessage(CHANNEL_ID, message)


def main():
    global CHANNEL_ID
    global CHANNEL_NAME

    CHANNEL_ID = getChannelsInfo(CHANNEL_NAME)['data'][0]['channelId']
    run(host='localhost', port=6600, debug=True)


main()