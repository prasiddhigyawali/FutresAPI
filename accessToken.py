import requests
from configparser import ConfigParser

parser = ConfigParser()
parser.read('db.ini')


host = parser.get('geomedb', 'url')
user = parser.get('geomedb', 'Username')
passwd = parser.get('geomedb', 'Password')
token_url = parser.get('geomedb', 'accessToken_url')

url = requests.get(token_url)
payload = {'client_id':parser.get('geomedb', 'client_id'), 
        'grant_type':parser.get('geomedb', 'grant_type'),
        'username': user,
        'password':passwd}
res = requests.post(token_url, data = payload)
print(res.json()["access_token"])
