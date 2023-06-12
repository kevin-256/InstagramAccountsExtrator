from datetime import date
import json, sys, subprocess, re, platform

actions = {0: 'followers',
           1: 'followings'}

def copyToClipboard(text):
    if platform.system()=='Linux' or platform.system()=='Darwin':
        subprocess.run("pbcopy", text=True, input=text)
    elif platform.system()=='Windows':
        subprocess.run("clip", text=True, input=text)
    else:
        print('error coping to clipboard, copy manually\ntext inside dash')
        print('----------------------------------------')
        print(text)
        print('----------------------------------------')


def usernameMatch(username):
    return re.match(r'^[\w](?!.*?\.{2})[\w.]{1,28}[\w]$',username)

def fileNameMatch(fileName):
    return re.match(r'^[\w](?!.*?\.{2})[\w.]{1,28}[\w]_[0-9]{4}_[0-9]{2}_[0-9]{2}.json$',fileName)

def decideFollowersFollowing():
    inputUser = ''
    while True:
        inputUser = input('Choose between:\n  0-Followers\n  1-Following\n>')
        try:
            if actions[int(inputUser)] != None:
                return actions[int(inputUser)]
        except:
            pass
        print('Invalid Input')

def generateJavascriptFor(user):
    javascriptTemplateFile = open(f'getFollowersFollowing.js', 'r', encoding="utf8")
    copyToClipboard(javascriptTemplateFile.read().replace('&&username&&', user))
    input(f'Paste the code in the javascript console on a browser with https://instagram.com page and press enter')
    copyToClipboard(f"copy({decideFollowersFollowing()})")
    #generate javascript code to get users
    javascriptTemplateFile.close()
    input('Paste the code in the javascript console and press enter')
    input(f'Paste the list of users in the {user}_{date.today().strftime("%Y_%m_%d")}.json file and save it')

def twoUsers(user1, user2):
    user1List = oneUser(user1)
    user2List = oneUser(user2)
    count = 0
    print('User1 list lenght: '+ str(len(user1List)))
    print('User2 list lenght: '+ str(len(user2List)))
    for user in user1List:
        for otherUser in user2List:
            if(user['username'] == otherUser['username']):
                print(user['username'])
                count+=1
                break
    print('common users count: ' + str(count))

def oneUser(user):
    #creation of file for the two users
    open(f'{user}_{date.today().strftime("%Y_%m_%d")}.json', 'w', encoding="utf8").close()
    generateJavascriptFor(user)
    return getListFromFile(f'{user}_{date.today().strftime("%Y_%m_%d")}.json')

def getListFromFile(fileName):
    userFile = open(fileName, 'r', encoding="utf8")
    userList = json.loads(userFile.read())
    userFile.close()
    return userList

if len(sys.argv) == 3 and sys.argv[1] == sys.argv[2]:
    print("username should be different")
elif len(sys.argv) == 3:
    if not usernameMatch(sys.argv[1]):
        print(f'username {sys.argv[1]} not valid')
    elif not usernameMatch(sys.argv[2]):
        print(f'username {sys.argv[2]} not valid')
    else:
        twoUsers(sys.argv[1],sys.argv[2])
elif len(sys.argv) == 2 and sys.argv[1].endswith('.json'):
    if fileNameMatch(sys.argv[1]):
        count = 0
        for user in getListFromFile(sys.argv[1]):
            count+=1
            print(user['username'])
        print(f'User list count: {count}')
    else:
        print()
elif len(sys.argv) == 2:
    if not usernameMatch(sys.argv[1]):
        print(f'username {sys.argv[1]} not valid')
    else:
        count = 0
        for user in oneUser(sys.argv[1]):
            count+=1
            print(user['username'])
        print(f'User list count: {count}')
else:
    print("  Pass two username to the script to get common followers/following list")
    print("    python commonUsers.py <user1> <user2>")
    print("  Pass one username to the script to get the followers/following list")
    print("    python commonUsers.py <user1>")
    print("  Pass one file to the script to get the followers/following list")
    print("    python commonUsers.py <filename>.json\n")    
