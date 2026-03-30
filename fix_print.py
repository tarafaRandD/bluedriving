import re

files = ['bluedriving.py', 'bluedrivingWebServer.py', 'getCoordinatesFromAddress.py', 'manageDB.py']

for file in files:
    with open(file, 'r') as f:
        content = f.read()
    content = re.sub(r"print '([^']*)'", r"print('\1')", content)
    with open(file, 'w') as f:
        f.write(content)

print('Print statements updated')