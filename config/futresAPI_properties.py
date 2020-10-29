import configparser
import parser
from configparser import SafeConfigParser

parser = SafeConfigParser()
parser.read('db.ini')

host = parser.get('geomedb', 'url')
user = parser.get('geomedb', 'Username')
passwd = parser.get('geomedb', 'Password')



print(f'Host: {host}')
print(f'User: {user}')
print(f'Password: {passwd}')