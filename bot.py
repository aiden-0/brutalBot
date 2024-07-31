import discord
import requests
import asyncio
import os
import certifi
from dotenv import load_dotenv
from pymongo import MongoClient
from discord.ext import commands, tasks
from test import getPuuid, latestMatchStats, getMatchid

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
MONGODB_URL = os.getenv('MONGODB_URL')


client = MongoClient(MONGODB_URL) #connecting to mongodb instance
db = client['test'] #switches to the test database
data = db['users'] # then switches to the users collection, stores player name and match id on seperate documents

bot = commands.Bot(command_prefix = "/", intents = discord.Intents.all())

@tasks.loop(seconds = 600)
async def checkNewMatch():
    for user in data.find():
        matchID_info = getMatchid(user['region'], user['name'],user['tag']) #checks for new matchid and compares it with old one stored in db
        matchID = matchID_info['matchid']
        if(user['matchID'] != (matchID)):
            channel = bot.get_channel(user['channelID'])
            dataUser = latestMatchStats(user['region'], user['name'],user['tag'])
            if(dataUser['outcome'] == "lost"):
                color = discord.Colour.red()
            else:
                color = discord.Colour.green()
            embed = discord.Embed(
                colour = color,
                title = f"{user['name']}#{user['tag']} has just {dataUser['outcome']} a comp game on {dataUser['map']} playing {dataUser['agent']}.\nScore: {dataUser['score']}",
                description = f"Rank: {dataUser['rank']}"
            )
            embed.set_thumbnail(url = dataUser['agentpic'])
            embed.add_field(name="Score", value= "```"+ str(dataUser['scorestat']) + "```", inline=True)
            embed.add_field(name="Kills", value= "```"+ str(dataUser['kills']) + "```", inline=True)
            embed.add_field(name="Deaths", value= "```"+ str(dataUser['deaths']) + "```", inline=True)
            embed.add_field(name="Assists", value= "```"+ str(dataUser['assists']) + "```", inline=True)
            embed.add_field(name="HS %", value= "```" + str(dataUser['hs'])+ "```", inline=True)
            embed.add_field(name="K/D", value= "```" + str(dataUser['kd']) + "```", inline=True)
            await channel.send(embed=embed)
            data.update_one({'_id': user['_id']}, {'$set': {'matchID': matchID}})
        if(matchID_info['remaining'] < 11):
            await asyncio.sleep(matchID_info['reset'])


    
@bot.command(name = 'helpbrutal')
async def helpbrutal(ctx):
    await ctx.send(
            f"Commands are:\n"
            "/latestmatch {riot name} {tag} {region}\n"
            f"This will provide the latest comp match stats\n"
            "/adduser {riot name} {tag} {region}\n"
            "This will add user to the tracker and notfies and displays stats when user just finished a comp game in channel where command was used"
                       )



@bot.command(name = 'latestmatch')
async def latest_match(ctx,*,input: str):
    info = input.split(" ")
    tag = info[-2]
    region = info[-1]
    size = len(info)
    nameList = info[:size -2]
    name = " ".join(nameList)
    matchID_info = getMatchid(region, name, tag)
    if(matchID_info == 404):
        await ctx.send("Error fetching, double check spelling")
        return
    elif(matchID_info == None):
        await ctx.send(f"Was not able to find {name}#{tag}. Make sure typed correctly")
        return
    
    matchID = matchID_info['matchid']
    dataUser = latestMatchStats(region, name,tag)
    if(dataUser['outcome'] == "lost"):
        color = discord.Colour.red()
    else:
        color = discord.Colour.green()
    embed = discord.Embed(
                colour = color,
                title = f"{name}#{tag} {dataUser['outcome']} their last comp game on {dataUser['map']} playing {dataUser['agent']}.\nScore: {dataUser['score']}",
                description = f"Rank: {dataUser['rank']}"
            )
    embed.set_thumbnail(url = dataUser['agentpic'])
    embed.add_field(name="Score", value= "```"+ str(dataUser['scorestat']) + "```", inline=True)
    embed.add_field(name="Kills", value= "```"+ str(dataUser['kills']) + "```", inline=True)
    embed.add_field(name="Deaths", value= "```"+ str(dataUser['deaths']) + "```", inline=True)
    embed.add_field(name="Assists", value= "```"+ str(dataUser['assists']) + "```", inline=True)
    embed.add_field(name="HS %", value= "```" + str(dataUser['hs'])+ "```", inline=True)
    embed.add_field(name="K/D", value= "```" + str(dataUser['kd']) + "```", inline=True)
    
    await ctx.send(embed=embed)
    
@bot.command(name = 'adduser')
async def addUser(ctx,*,input: str):
    info = input.split(" ")
    tag = info[-2]
    region = info[-1]
    size = len(info)
    nameList = info[:size -2]
    name = " ".join(nameList)
    matchID_info = getMatchid(region, name, tag)
    if(matchID_info == 404):
        await ctx.send("Error with api, double check spelling")
        return

    matchID = matchID_info['matchid']
    user = data.find_one({"name": name,'tag': tag})
    if user != None: #case for duplicates
        await ctx.send("```User already exist in database```")
        return 
    if(matchID == None):
        await ctx.send("Username doesn't exist")
        return 
    else:
        data.insert_one({"name": name,"tag": tag,"matchID": matchID, "region": region,"channelID": ctx.channel.id})
        await ctx.send("Successfully added " + name + '#'+ tag + " this channel will now be notfied when they have finished a comp game!" )
    

@bot.command(name = 'howmany')
async def howMany(ctx):
    await ctx.send(f"I'm in {(len(bot.guilds))} servers!")

@bot.event
async def on_ready():
    checkNewMatch.start()
    print("ready")


bot.run(DISCORD_TOKEN)
