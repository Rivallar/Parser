import requests
from kafka import KafkaProducer, KafkaConsumer
from json import dumps, loads

from config import settings


def token_from_twitch():

    """Gets fresh token from twitch and sends it to kafka"""

    url = 'https://id.twitch.tv/oauth2/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'client_id': settings.TWITCH_CLIENT_ID,
        'client_secret': settings.TWITCH_CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }

    result = requests.post(url, headers=headers, data=data)
    token = result.json()['access_token']

    producer = KafkaProducer(bootstrap_servers=[settings.KAFKA_BROKER],
                             value_serializer=lambda x: dumps(x).encode('utf-8'))
    producer.send('twitch_token', token)
    producer.close()

    return token


def get_token():

    """Obtains token from kafka or fresh token from twitch"""

    konsumer = KafkaConsumer('twitch_token',
                             bootstrap_servers=[settings.KAFKA_BROKER],
                             auto_offset_reset='earliest',
                             enable_auto_commit=True,
                             # group_id='my-group',
                             value_deserializer=lambda x: loads(x.decode('utf-8')),
                             consumer_timeout_ms=1000
                             )
    token = ''
    for message in konsumer:
        token = message.value
    if not token:
        token = token_from_twitch()

    return token


def make_headers(token):
    headers = {'Authorization': f'Bearer {token}',
               'Client-Id': settings.TWITCH_CLIENT_ID}

    return headers


def get_from_twitch(url, headers, limit=99999999):

    """Sends get-requests to different twitch api-endpoints. Loops through pages if there are more then 100 results"""

    response = requests.get(url, headers=headers).json()
    data = response['data']
    count = 1
    while response['pagination'] and count < limit:
        cursor = f'&after={response["pagination"]["cursor"]}'
        response = requests.get(url + cursor, headers=headers).json()
        data.extend(response['data'])
        count += 1
    return data


def chunk_of_games(request_result):

    """Fixes image url"""

    chunk = []
    for game in request_result['data']:
        game['box_art_url'] = game['box_art_url'].replace('{width}x{height}', '285x380')
        chunk.append(game)
    return chunk


def get_all_games(token):

    """Returns all active games. Sends whole bunch to kafka."""

    base_url = 'https://api.twitch.tv/helix/games/top?first=100'
    headers = make_headers(token)

    game_list = get_from_twitch(base_url, headers)

    producer = KafkaProducer(bootstrap_servers=[settings.KAFKA_BROKER],
                             value_serializer=lambda x: dumps(x).encode('utf-8'))

    producer.send('twitch_games', game_list)
    producer.close()
    return game_list


def read_all_games(token):

    """Gets all active games either from kafka or right from twitch"""

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

    """Gets id of a game by its name."""

    url = f'https://api.twitch.tv/helix/games?name={game_name}'
    result = requests.get(url, headers=make_headers(token)).json()

    return int(result['data'][0]['id'])


def get_game_streams(game_id, token, language=None):

    """Returns active streams of a certain game (by its id). Can filter by stream language"""

    url = f'https://api.twitch.tv/helix/streams?game_id={game_id}&type=live&first=100'
    if language:
        url += f'&language={language}'
    headers = make_headers(token)

    streams = get_from_twitch(url, headers)

    return streams


def search_game(token, query):

    """Get games with names matching query condition."""

    url = f'https://api.twitch.tv/helix/search/categories?query={query}&first=100'
    headers = make_headers(token)
    search_result = get_from_twitch(url, headers, limit=3)

    return search_result


def search_channels(token, query):

    """Gets live streams matching query condition. Matches may be either in game name or in stream name."""

    url = f'https://api.twitch.tv/helix/search/channels?query={query}&first=100&live_only=true'

    headers = make_headers(token)
    channels = get_from_twitch(url, headers)

    return channels


def get_user(token, user_id=None, login=None):

    """Get single user info. Queries either by user id or by its login."""

    url = f'https://api.twitch.tv/helix/users?'
    if user_id:
        url += f'id={user_id}'
    else:
        url += f'login={login}'

    response = requests.get(url, headers=make_headers(token)).json()
    return response['data']

