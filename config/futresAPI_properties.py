from ConfigParser import SafeConfigParser

parser = SafeConfigParser()
parser.read('db.ini')


host = parser.get('geomedb', 'url')
user = parser.get('geomedb', 'Username')
passwd = parser.get('geomedb', 'Password')

print(host)
print(user)
print(passwd)