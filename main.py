# Укажите персональный токен JetBrain Space
API_TOKEN = "eyJhbGciOiJSUzUxMiJ9.eyJzdWIiOiI0MXFCcmg0VE5sV0MiLCJhdWQiOiJjaXJjbGV0LXdlYi11aSIsIm9yZ0RvbWFpbiI6IndvcmtsZSIsIm5hbWUiOiJtc2hhbXNodXJpbkB3b3JrbGUucnUiLCJpc3MiOiJodHRwczpcL1wvamV0YnJhaW5zLnNwYWNlIiwicGVybV90b2tlbiI6IjFyNVFsSTEzNWtFWiIsInByaW5jaXBhbF90eXBlIjoiVVNFUiIsImlhdCI6MTYwMzI4ODU0N30.cpHx4odaYJjJAcWiV91_t-W-cDQF-CGBOCulyRcgPZgC7GPIOlXz1-r-bPCRvjECurbi28gKh8c4OOP6jmg4KoJ2xRRIVcFRfAqKN3G1EPjaevheMZXLCi3dtoan5jYSQTMiif04d8E8wkWMlSLH3ZmAmT3b-7M8L6Gkr7Ospx0"
ORGANIZATION_NAME = "workle"  # Укажите наименование организации

PUSH_ROUTE_NAMES = {
    # DEFAULT — обязательный параметр,
    # который указывает, куда отправлять
    # данные из других branch`ей
    'DEFAULT': "it_github_bot"
}

PULL_ROUTE_NAMES = {
    # DEFAULT — обязательный параметр,
    # который указывает, куда отправлять
    # данные из других branch`ей
    'DEFAULT': "it_github_bot"
}

import requests
import json
from bottle import route, run, post, request

PUSH_ROUTE_IDS = {}
PULL_ROUTE_IDS = {}
REQUEST_HEADERS = {
    'Authorization': "Bearer {0}".format(API_TOKEN),
    'Accept': 'application/json',
}


def setChannelsIds(routesDict):
    result = {}
    for key in routesDict.keys():
        result[key] = getChannelsInfo(routesDict[key])['data'][0]['channelId']
    return result


def getChannelsInfo(nameOfChannel=""):
    global ORGANIZATION_NAME
    global REQUEST_HEADERS

    query = "https://{0}.jetbrains.space/api/http/chats/channels/all-channels?query={1}".format(
        ORGANIZATION_NAME, nameOfChannel)
    print("Получение информации о каналах/канале...")

    response = requests.get(query, headers=REQUEST_HEADERS)
    print("Запрос успешно отправлен. Ответ сервера:\n{0}\n\n".format(
        json.dumps(json.loads(response.text), sort_keys=True, indent=4)))

    return json.loads(response.text)


def sendMessage(channelId, message):
    global ORGANIZATION_NAME
    global REQUEST_HEADERS

    query = "https://{0}.jetbrains.space/api/http/chats/channels/{1}/messages".format(
        ORGANIZATION_NAME, channelId)

    print("Отправка сообщения:\n{0}\n\n".format(message))
    dataToSend = {"text": message}
    response = requests.post(query, headers=REQUEST_HEADERS, json=dataToSend)
    print("Cообщение успешно отправлено . Ответ сервера:\n{0}\n\n".format(
        json.dumps(json.loads(response.text), sort_keys=True, indent=4)))

    return json.loads(response.text)


@post('/push')
def doPostPush():
    global PUSH_ROUTE_NAMES

    print("Произолшло событие GitHub: \n{0}\n\n".format(
        json.dumps(request.json, sort_keys=True, indent=4)))

    # Заполнение полей
    message = ''
    jsonedData = json.load(request.body)
    username = jsonedData['head_commit']['author']['username']
    fullname = jsonedData['head_commit']['author']['name']
    commitsCount = len(jsonedData['commits'])
    sLetter = "" if commitsCount != 1 else 's'
    branchName = jsonedData['ref'].split('/')[-1]
    commits = jsonedData['commits']

    userLink = jsonedData["sender"]["html_url"]
    commitsCountLink = jsonedData["compare"]
    repositoryLink = jsonedData["repository"][
        "html_url"] + '/tree/' + branchName

    ### Поля
    # 0 — Имя пользователя
    # 1 — Полное имя
    # 2 — Количество комитов
    # 3 — Буква s, которая отображает мн. число
    # 4 — Ветка
    ### Cссылки
    # 5 — Ссылка на пользователя
    # 6 — Ссылка на изменения
    # 7 — Ссылка на репозиторий
    headerFormat = ">**[{0} ({1})]({5})**\n>[{2} new commit{3}]({6}) pushed to [{4}]({7})"

    ### Поля
    # 0 — Первые 7 символов id коммита
    # 1 — Заголовок коммита
    commitFormat = "\n>\xa0\xa0\xa0[{0}]({2}) — {1}"

    # Формирование сообщения
    message += headerFormat.format(username, fullname, commitsCount, sLetter,
                                   branchName, userLink, commitsCountLink,
                                   repositoryLink)
    for item in commits:
        message += commitFormat.format(item['id'][0:6], item['message'],
                                       item["url"])

    try:
        sendMessage(PUSH_ROUTE_IDS[branchName], message)
    except Exception:
        sendMessage(PUSH_ROUTE_IDS['DEFAULT'], message)


@post('/pull')
def doPostPull():
    print(json.dumps(json.load(request.body), sort_keys=True, indent=4))
    pass


def main():
    global PUSH_ROUTE_IDS
    global PUSH_ROUTE_NAMES
    PUSH_ROUTE_IDS = setChannelsIds(PUSH_ROUTE_NAMES)

    global PULL_ROUTE_IDS
    global PULL_ROUTE_NAMES
    PULL_ROUTE_IDS = setChannelsIds(PULL_ROUTE_NAMES)

    run(host='localhost', port=6600, debug=True)


main()