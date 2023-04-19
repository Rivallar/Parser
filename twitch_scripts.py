import requests
from kafka import KafkaProducer, KafkaConsumer
from json import dumps, loads

from config import settings


def get_token():
    url = 'https://id.twitch.tv/oauth2/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'client_id': 'dz3dnoqtnunqzyjfadabuhgrhuvkk3',
        'client_secret': '8wnmjys0j4qjnogo0so5rewigy23t7',
        'grant_type': 'client_credentials'
    }

    result = requests.post(url, headers=headers, data=data)
    if result.status_code == 200:
        token = result.json()['access_token']
        return token
    else:
        return


def chunk_of_games(request_result):
    chunk = []
    for game in request_result['data']:
        game['box_art_url'] = game['box_art_url'].replace('{width}x{height}', '285x380')
        chunk.append(game)
    return chunk


def get_all_games(token):
    base_url = 'https://api.twitch.tv/helix/games/top'
    limit = '?first=100'
    headers = {'Authorization': f'Bearer {token}',
               'Client-Id': 'dz3dnoqtnunqzyjfadabuhgrhuvkk3'}

    result = requests.get(base_url + limit, headers=headers).json()
    game_list = chunk_of_games(result)

    while result['pagination']:
        cursor = f'&after={result["pagination"]["cursor"]}'
        result = requests.get(base_url + limit + cursor, headers=headers).json()
        game_list.extend(chunk_of_games(result))

    producer = KafkaProducer(bootstrap_servers=[settings.KAFKA_BROKER],
                             value_serializer=lambda x: dumps(x).encode('utf-8'))

    producer.send('twitch_games', game_list)
    producer.close()
    return game_list


def read_all_games(token):
    konsumer = KafkaConsumer('twitch_games',
                             bootstrap_servers=[settings.KAFKA_BROKER],
                             auto_offset_reset='earliest',
                             enable_auto_commit=True,
                             # group_id='my-group',
                             value_deserializer=lambda x: loads(x.decode('utf-8')),
                             consumer_timeout_ms=1000
                             )
    games_in_kafka = ''
    for message in konsumer:
        games_in_kafka = message.value

    if not games_in_kafka:
        games_in_kafka = get_all_games(token)

    return games_in_kafka


def get_game_id(game_name, token):
    url = f'https://api.twitch.tv/helix/games?name={game_name}'
    headers = {'Authorization': f'Bearer {token}',
               'Client-Id': 'dz3dnoqtnunqzyjfadabuhgrhuvkk3'}
    result = requests.get(url, headers=headers).json()
    return int(result['data'][0]['id'])


def get_game_streams(game_id, token, language=None):
    url = f'https://api.twitch.tv/helix/streams?game_id={game_id}&type=live&first=100'
    if language:
        url += f'&language={language}'
    headers = {'Authorization': f'Bearer {token}',
               'Client-Id': 'dz3dnoqtnunqzyjfadabuhgrhuvkk3'}
    result = requests.get(url, headers=headers).json()
    streams = result['data']
    while result['pagination']:
        cursor = f'&after={result["pagination"]["cursor"]}'
        result = requests.get(url + cursor, headers=headers).json()
        streams.extend(result['data'])
    return streams


def search_game(token, query):
    url = f'https://api.twitch.tv/helix/search/categories?query={query}&first=100'
    headers = {'Authorization': f'Bearer {token}',
               'Client-Id': 'dz3dnoqtnunqzyjfadabuhgrhuvkk3'}
    response = requests.get(url, headers=headers).json()
    search_result = response['data']
    count = 1
    while response['pagination'] and count < 3:
        cursor = f'&after={response["pagination"]["cursor"]}'
        result = requests.get(url + cursor, headers=headers).json()
        search_result.extend(result['data'])
        count += 1
    return search_result


def search_channels(token, query):
    url = f'https://api.twitch.tv/helix/search/channels?query={query}&first=100&live_only=true'
    headers = {'Authorization': f'Bearer {token}',
               'Client-Id': 'dz3dnoqtnunqzyjfadabuhgrhuvkk3'}
    response = requests.get(url, headers=headers).json()
    search_result = response['data']
    while response['pagination']:
        cursor = f'&after={response["pagination"]["cursor"]}'
        result = requests.get(url + cursor, headers=headers).json()
        search_result.extend(result['data'])
    return search_result


def get_user(token, user_id=None, login=None):
    url = f'https://api.twitch.tv/helix/users?'
    if user_id:
        url += f'id={user_id}'
    else:
        url += f'login={login}'

    headers = {'Authorization': f'Bearer {token}',
               'Client-Id': 'dz3dnoqtnunqzyjfadabuhgrhuvkk3'}
    response = requests.get(url, headers=headers).json()
    return response['data']

