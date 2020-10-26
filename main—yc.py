#############################################
#          Настройки для работы             #
#        (обязательные параметры)           #
#############################################

# JETBRAINS_ORGANIZATION_DOMAIN_NAME —      #
# доменное имя организации JetBrains Space  #
JETBRAINS_ORGANIZATION_DOMAIN_NAME = ""

# JETBRAINS_CLIENT_ID — идентификатор бота, #
# который будет отправлять сообщения        #
# JETBRAINS_CLIENT_SECRET — секретный ключ  #
# бота                                      #
JETBRAINS_CLIENT_ID = ""
JETBRAINS_CLIENT_SECRET = ""

# Информация о ботах находится в Space:     #
# Administration → Applications             #
#############################################

#############################################
#           Направления сообщений           #
#############################################
# Внутри вы указываете перенаправления,     #
# используя следующий синтаксис             #
# "BRANCH_NAME" : "SPACE_CHAT_DISPLAY_NAME" #
#                                           #
# Чтобы отправлять все нефильтрованные      #
# ветки в определенный чат, укажите:        #
# "DEFAULT" : "SPACE_CHAT_DISPLAY_NAME"     #
#                                           #
# Чтобы игнорировать определенный branch    #
# укажите:                                  #
# "BRANCH_NAME" : None                      #
#                                           #
# Чтобы игнорировать branch`и, которые не   #
# прошли фильтрацию укажите:                #
# "DEFAULT" : None                          #
#############################################

#############################################
#             Push направления              #
#############################################
# Перенаправление по branch                 #
#############################################

PUSH_ROUTE_NAMES = {
    # DEFAULT — обязательный параметр,
    # который указывает, куда отправлять
    # данные из других branch`ей
    'DEFAULT': "it_github_bot"
}

#############################################
#             Pull направления              #
#############################################
# Перенаправление по branch, в который      #
# будут вливаться изменения из              #
# других ветвей                             #
#############################################

PULL_ROUTE_NAMES = {
    # DEFAULT — обязательный параметр,
    # который указывает, куда отправлять
    # данные из других branch`ей
    'DEFAULT': "it_github_bot"
}

#############################################

import requests
import json
import base64

# Служебные глобальные переменные (НЕ ИЗМЕНЯТЬ)

PUSH_ROUTE_IDS = {}
PULL_ROUTE_IDS = {}
JETBRAINS_API_TOKEN = ""
REQUEST_HEADERS = {
    'Authorization': "Bearer {0}".format(JETBRAINS_API_TOKEN),
    'Accept': 'application/json',
}


def getAccessToken():
    global JETBRAINS_ORGANIZATION_DOMAIN_NAME
    global JETBRAINS_CLIENT_ID
    global JETBRAINS_CLIENT_SECRET

    authorizationString = JETBRAINS_CLIENT_ID + ":" + JETBRAINS_CLIENT_SECRET
    bytesString = authorizationString.encode('ascii')
    base64String = base64.b64encode(bytesString).decode('ascii')

    query = "https://{0}.jetbrains.space/oauth/token".format(
        JETBRAINS_ORGANIZATION_DOMAIN_NAME)
    response = requests.post(
        query,
        data={
            'grant_type': 'client_credentials',
        },
        headers={'Authorization': 'Basic ' + base64String})

    return json.loads(response.text)['access_token']


def setChannelsIds(routesDict):
    result = {}
    for key in routesDict.keys():
        if (not routesDict[key]):
            result[key] = None
        else:
            result[key] = getChannelsInfo(
                routesDict[key])['data'][0]['channelId']
    return result


def getChannelsInfo(nameOfChannel=""):
    global JETBRAINS_ORGANIZATION_DOMAIN_NAME
    global REQUEST_HEADERS

    query = "https://{0}.jetbrains.space/api/http/chats/channels/all-channels?query={1}".format(
        JETBRAINS_ORGANIZATION_DOMAIN_NAME, nameOfChannel)

    response = requests.get(query, headers=REQUEST_HEADERS)

    return json.loads(response.text)


def sendMessage(channelId, message):
    if (not channelId):
        return

    global JETBRAINS_ORGANIZATION_DOMAIN_NAME
    global REQUEST_HEADERS

    query = "https://{0}.jetbrains.space/api/http/chats/channels/{1}/messages".format(
        JETBRAINS_ORGANIZATION_DOMAIN_NAME, channelId)

    dataToSend = {"text": message}
    response = requests.post(query, headers=REQUEST_HEADERS, json=dataToSend)

    return json.loads(response.text)


def findKey(_dict, key):
    filtered = list(filter(lambda item: item == key, _dict.keys()))
    return len(filtered) != 0


#############################################
#              Обработка событий            #
#############################################


def push(json):
    global PUSH_ROUTE_NAMES

    message = None

    jsonedData = json
    after = jsonedData['after']
    before = jsonedData['before']

    if (before == "0000000000000000000000000000000000000000"):
        ### Поля
        # 0 — пользователь
        # 1 — ссылка на пользователя
        # 2 — удаленная ветка
        messageFormat = ">**[{0}]({1})** created `{2}` branch"

        username = jsonedData['sender']['login']
        branchName = jsonedData['ref'].split('/')[-1]

        userLink = jsonedData["sender"]["html_url"]

        message = messageFormat.format(username, userLink, branchName)

    elif (after == "0000000000000000000000000000000000000000"):
        ### Поля
        # 0 — пользователь
        # 1 — ссылка на пользователя
        # 2 — удаленная ветка
        messageFormat = ">**[{0}]({1})** deleted `{2}` branch"

        username = jsonedData['sender']['login']
        branchName = jsonedData['ref'].split('/')[-1]

        userLink = jsonedData["sender"]["html_url"]

        message = messageFormat.format(username, userLink, branchName)

    elif (after != "0000000000000000000000000000000000000000"):
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
        messageFormat = ">**[{0}]({4})** pushed [{1} new commit{2}]({5}) pushed to [{3}]({6})"

        ### Поля
        # 0 — Первые 7 символов id коммита
        # 1 — Заголовок коммита
        commitFormat = "\n>\xa0\xa0\xa0[{0}]({2}) — {1}"

        username = jsonedData['sender']['login']
        commitsCount = len(jsonedData['commits'])
        sLetter = "" if commitsCount != 1 else 's'
        branchName = jsonedData['ref'].split('/')[-1]
        commits = jsonedData['commits']

        userLink = jsonedData["sender"]["html_url"]
        commitsCountLink = jsonedData["compare"]
        repositoryLink = jsonedData["repository"][
            "html_url"] + '/tree/' + branchName

        message = messageFormat.format(username, commitsCount, sLetter,
                                       branchName, userLink, commitsCountLink,
                                       repositoryLink)
        for item in commits:
            message += commitFormat.format(item['id'][0:6],
                                           item['message'].replace('\n', ' '),
                                           item["url"])

    if (not message):
        return

    if (findKey(PULL_ROUTE_IDS, branchName)):
        sendMessage(PULL_ROUTE_IDS[branchName], message)
    else:
        sendMessage(PULL_ROUTE_IDS['DEFAULT'], message)


def pull(json):
    jsonedData = json
    message = None

    action = jsonedData["action"]

    if (action == "opened"):
        ### Поля
        # 0 — пользователь
        # 1 — ссылка на пользователя
        # 2 — количество комитов
        # 3 — буква «s»
        # 4 — ссылка на комиты
        # 5 — ветка вливания
        # 6 — вливающая ветка
        # 7 — наименование запроса
        # 8 — ссылка на запрос
        messageFormat = ">**[{0}]({1})** wants to merge [{2} commit{3}]({4}) into `{5}` from `{6}` \n>Pull request **[“{7}”]({8})** has been created"

        sender = jsonedData['sender']['login']
        commits = jsonedData['pull_request']['commits']
        base = jsonedData['pull_request']['base']['ref']
        head = jsonedData['pull_request']['head']['ref']
        title = jsonedData['pull_request']['title']

        link = jsonedData['pull_request']['_links']['html']['href']
        commitsLink = link + "/commits"
        senderLink = jsonedData['sender']['html_url']

        message = messageFormat.format(sender, senderLink, commits,
                                       '' if commits == 1 else 's',
                                       commitsLink, base, head, title, link)

    if (action == "reopened"):
        ### Поля
        # 0 — пользователь
        # 1 — ссылка на пользователя
        # 2 — количество комитов
        # 3 — буква «s»
        # 4 — ссылка на комиты
        # 5 — ветка вливания
        # 6 — вливающая ветка
        # 7 — наименование запроса
        # 8 — ссылка на запрос
        messageFormat = ">**[{0}]({1})** wants to merge [{2} commit{3}]({4}) into `{5}` from `{6}` \n>Pull request **[“{7}”]({8})** has been reopened"

        sender = jsonedData['sender']['login']
        commits = jsonedData['pull_request']['commits']
        base = jsonedData['pull_request']['base']['ref']
        head = jsonedData['pull_request']['head']['ref']
        title = jsonedData['pull_request']['title']

        link = jsonedData['pull_request']['_links']['html']['href']
        commitsLink = link + "/commits"
        senderLink = jsonedData['sender']['html_url']

        message = messageFormat.format(sender, senderLink, commits,
                                       '' if commits == 1 else 's',
                                       commitsLink, base, head, title, link)

    if (action == "closed"):

        merged = jsonedData['pull_request']['merged']

        if (merged):
            ### Поля
            # 0 — пользователь
            # 1 — ссылка на пользователя
            # 2 — наименование запроса
            # 3 — ссылка на запрос
            messageFormat = ">**[{0}]({1})** merged pull request **[“{2}”]({3})**"

            title = head = jsonedData['pull_request']['title']
            merged_by = jsonedData['pull_request']['merged_by']['login']

            senderLink = jsonedData['pull_request']['merged_by']['html_url']
            link = jsonedData['pull_request']['_links']['html']['href']

            base = jsonedData['pull_request']['base']['ref']

            message = messageFormat.format(merged_by, senderLink, title, link)

        else:
            ### Поля
            # 0 — пользователь
            # 1 — ссылка на пользователя
            # 2 — наименование запроса
            # 3 — ссылка на запрос
            messageFormat = ">**[{0}]({1})** closed pull request **[“{2}”]({3})**"

            title = head = jsonedData['pull_request']['title']
            sender = jsonedData['sender']['login']

            senderLink = jsonedData['sender']['html_url']
            link = jsonedData['pull_request']['_links']['html']['href']

            base = jsonedData['pull_request']['base']['ref']

            message = messageFormat.format(sender, senderLink, title, link)

    if (not message):
        return

    if (findKey(PULL_ROUTE_IDS, base)):
        sendMessage(PULL_ROUTE_IDS[base], message)
    else:
        sendMessage(PULL_ROUTE_IDS['DEFAULT'], message)


def getIds():
    global JETBRAINS_API_TOKEN
    global REQUEST_HEADERS
    JETBRAINS_API_TOKEN = getAccessToken()
    REQUEST_HEADERS['Authorization'] = 'Bearer ' + JETBRAINS_API_TOKEN

    global PUSH_ROUTE_IDS
    global PUSH_ROUTE_NAMES
    PUSH_ROUTE_IDS = setChannelsIds(PUSH_ROUTE_NAMES)

    global PULL_ROUTE_IDS
    global PULL_ROUTE_NAMES
    PULL_ROUTE_IDS = setChannelsIds(PULL_ROUTE_NAMES)


#############################################
#                Точка входа                #
#############################################


def doPost(event, context):
    getIds()
    jsonedData = json.loads(event['body'])

    if (findKey(jsonedData, 'pull_request')):
        pull(jsonedData)

    if (findKey(jsonedData, 'commits')):
        push(jsonedData)