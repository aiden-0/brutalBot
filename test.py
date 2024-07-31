import requests
import time
import asyncio
import aiohttp
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
api_key = os.getenv('API_KEY')
MONGODB_URL = os.getenv('MONGODB_URL')
headers = {
        "Authorization": api_key,
    }
client = MongoClient(MONGODB_URL) #connecting to mongodb instance
db = client['test'] #switches to the test database
data = db['users'] # then switches to the users collection, stores player name and match id on seperate documents

# testing api call times
# start = time.time()
# url = "https://api.henrikdev.xyz/valorant/v1/account/brutal/111" 
# response = requests.get(url, headers=headers)
# end = time.time()
# print(end-start)


def getPuuid(name, tag):
    url = f"https://api.henrikdev.xyz/valorant/v1/account/{name}/{tag}" 
    response = requests.get(url, headers=headers) #get request set to response
    if(response.status_code == 200): # if it executes good then it returns the player id.
        return response.json()['data']['puuid']
    else:
        return None



def getMatchid(region, name, tag):
    url = f"https://api.henrikdev.xyz/valorant/v3/matches/{region}/{name}/{tag}?mode=competitive&size=1"
    response = requests.get(url, headers=headers)
    if(response.status_code == 404):
        return 404
    elif(response.status_code == 200):
        return{'matchid': response.json()['data'][0]['metadata']['matchid'],
                'remaining': int(response.headers.get('x-ratelimit-remaining')),
                'reset': int(response.headers.get('x-ratelimit-reset'))
        }
    else:
        return None
    
        
def latestMatchStats(region,name,tag):
    url = f"https://api.henrikdev.xyz/valorant/v3/matches/{region}/{name}/{tag}?mode=competitive&size=1"
    response = requests.get(url, headers=headers)
    data = response.json()['data'][0]['players']
    for player in data['all_players']: #iterates through each player profile in LATEST MATCH and checks for certain puuids
        if((player['name'] == name) and (player['tag'] == tag)):
            teamColor = player['team'].lower()
            if(response.json()['data'][0]['teams'][teamColor]['has_won'] == True):
                score = str(response.json()['data'][0]['teams'][teamColor]['rounds_won']) + "-" + str(response.json()['data'][0]['teams'][teamColor]['rounds_lost'])
                outcome = "won"
            else:
                outcome = "lost"
                score = str(response.json()['data'][0]['teams'][teamColor]['rounds_won']) + "-" + str(response.json()['data'][0]['teams'][teamColor]['rounds_'])
            return{ # returns a dictionary, with all the stats of the latest match.
                'agent': player['character'],
                'agentpic': player['assets']['agent']['small'],
                'rank': player['currenttier_patched'],
                'map': response.json()['data'][0]['metadata']['map'],
                'scorestat': player['stats']['score'], 
                'kills': player['stats']['kills'],
                'deaths': player['stats']['deaths'],
                'assists': player['stats']['assists'],
                'kd': round((player['stats']['kills'] / player['stats']['deaths']),2),
                'hs': (round((player['stats']['headshots'] / (player['stats']['bodyshots'] + player['stats']['headshots'] + player['stats']['legshots'])) * 100)),
                'outcome': outcome,
                'score': score
                }

def addUser(name, tag, region):
    matchID = getMatchid(region, name,tag)['matchid']
    user = data.find_one({"name": name,'tag': tag})
    if user != None: #case for duplicates
        return ("already exists")
    if(matchID == None):
        return ("does not exist") 
    else:
        data.insert_one({"name": name,"tag": tag,"matchID": matchID, "region": region})
        return("sucessfully added")



# testing api call times
# start = time.time()
# print(type((getMatchid("na","chaewon buff", "4885")['remaining'])))
# end = time.time()
# print(end-start)







        
        
    




 


     