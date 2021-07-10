from problox import Problox
import json, threading, requests, ctypes, time


config = json.loads(open('config.json', 'r').read().strip())

class Main:

    def __init__(self, useThreading, GameID, Cookies):
        if config['multiple_clients'] == True:
            self.useThreading = True

        self.CurrentClients = 0
        self.SuccessfulLikes = 0
        self.Attempts = 0
        self.Done = False
        self.useThreading = useThreading
        self.GameID = GameID
        self.Cookies = Cookies

    def AttemptLike(self, cookie):
        rbx = Problox.from_cookiefile(cookie)
        user_info = rbx.request(method="GET", url="https://users.roblox.com/v1/users/authenticated").json()
        name = user_info['name']

        client = rbx.join_game(self.GameID, locale="en_en")

        self.CurrentClients += 1
        client.wait_for(config['load_timeout'])
        client.close()
        self.CurrentClients -= 1
        self.Attempts += 1

        res = rbx.request('POST', f'https://www.roblox.com/voting/vote?assetId={self.GameID}&vote=true').json()

        if res['Success'] == True:
            self.SuccessfulLikes += 1
            print(f'[SUCCESS] User: {name} Game: {self.GameID}')
        else:
            print(f'[FAILED] User: {name} Game: {self.GameID}')

        self.UpdateConsole()
        

    def UpdateConsole(self):
        Title = f'Attempts: {self.Attempts} | Successful Likes: {self.SuccessfulLikes}'
        ctypes.windll.kernel32.SetConsoleTitleW(Title)


if __name__ == "__main__":
    Cookies = open(config['cookie_file'],'r').read().strip().split('\n')
    GameID = config['game_id']
    Program = Main(config['multiple_clients'], GameID, Cookies)
    
    GameInfo = requests.get(f'https://api.roblox.com/marketplace/productinfo?assetId={GameID}').json()
    GameName = GameInfo['Name']

    print('-------------------------------------------------------------' + ('-' * len(GameName)))
    print(f'(STARTED) Loaded {len(Cookies)} cookies. Attempting to bot "{GameName}".')
    print('-------------------------------------------------------------' + ('-' * len(GameName)))

    Program.UpdateConsole()

    def Thread():
        while len(Cookies) > 0:
            if Program.CurrentClients < config['max_clients']:
                try:
                    Program.AttemptLike(Cookies.pop(0))
                except Exception as e:
                    pass
                if len(Cookies) < 1 and Program.Done == False:
                    Program.Done = True
                    time.sleep(1)
                    print(f"Done! Liked {Program.SuccessfulLikes} times.")
                    exit()

    Threads = []

    for i in range(config['threads']):
        Threads.append(threading.Thread(target=Thread))

    for thread in Threads:
        thread.start()