import discord
import os
import re
import datetime
import psycopg2
import asyncio
from os.path import join, dirname
from dotenv import load_dotenv

load_dotenv(verbose=True)
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

TOKEN = os.environ.get("TOKEN")

client = discord.Client()

Data = []

def searchGuild(guild_id):
    with psycopg2.connect('postgresql://admin:admin@localhost:15432/admin') as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM progress_app.guild WHERE id=%s", (guild_id, ))
            userChecker = cur.fetchone()
            return userChecker
            
def addGuild(guild, uid):
    with psycopg2.connect('postgresql://admin:admin@localhost:15432/admin') as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO progress_app.guild VALUES (%s, %s, %s, %s)", (guild.id, guild.name, [uid], guild.system_channel.id))
        conn.commit()

def searchGuildMember(guild_id, uid):
    with psycopg2.connect('postgresql://admin:admin@localhost:15432/admin') as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_ids FROM progress_app.guild WHERE id=%s", (guild_id, ))
            memberList = list(cur.fetchone()[0])
            return (uid in memberList)

def searchUser(userId):
    with psycopg2.connect('postgresql://admin:admin@localhost:15432/admin') as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM progress_app.user WHERE id=%s", (userId, ))
            userChecker = cur.fetchone()
            return userChecker
            
def addUser(id, name, guild_id):
    with psycopg2.connect('postgresql://admin:admin@localhost:15432/admin') as conn:
        with conn.cursor() as cur:
            if not searchUser(id):
                cur.execute("INSERT INTO progress_app.user VALUES (%s, %s, '{}')", (id, name))
            cur.execute("SELECT user_ids FROM progress_app.guild WHERE id=%s", (guild_id, ))
            guildMemberList = list(cur.fetchone()[0])
            if not id in guildMemberList:
                guildMemberList.append(id)
                cur.execute("UPDATE progress_app.guild SET user_ids=%s WHERE id=%s", (guildMemberList, guild_id))
        conn.commit()

def searchTask(userId, taskName):
    with psycopg2.connect('postgresql://admin:admin@localhost:15432/admin') as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM progress_app.task WHERE user_id=%s AND task_name=%s", (userId, taskName))
            taskColumn = cur.fetchone()
            if taskColumn:
                return taskColumn[0]
            else:
                return addTask(userId, taskName)

def addTask(userId, taskName):
    with psycopg2.connect('postgresql://admin:admin@localhost:15432/admin') as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO progress_app.task (task_name, user_id, duration) VALUES (%s, %s, %s)", (taskName, userId, datetime.timedelta()))
            cur.execute("SELECT task_ids FROM progress_app.user WHERE id=%s", (userId, ))
            task_list = list(cur.fetchone()[0])
            cur.execute("SELECT MAX(id) FROM progress_app.task")
            task_id = cur.fetchone()[0]
            task_list.append(task_id)
            cur.execute("UPDATE progress_app.user SET task_ids=%s WHERE id=%s", (task_list, userId))
            return task_id
        conn.commit()
    
def addProgressTime(taskId, duration):
    with psycopg2.connect('postgresql://admin:admin@localhost:15432/admin') as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE progress_app.task SET duration=(duration+%s) WHERE id=%s", (duration, taskId))
        conn.commit()

def setNotifyChannel(guild, channel):
    with psycopg2.connect('postgresql://admin:admin@localhost:15432/admin') as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE progress_app.guild SET notify_channel=%s WHERE id=%s", (channel.id, guild.id))
        conn.commit()

async def reportTheirProgress():
    for data in Data:
        duration = datetime.datetime.now() - datetime.datetime.fromisoformat(data['start_at'])
        addProgressTime(data['task_id'], duration)
    with psycopg2.connect('postgresql://admin:admin@localhost:15432/admin') as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM progress_app.guild")
            guild_list = cur.fetchall()
            for guild_table in guild_list:
                channel = client.get_channel(guild_table[3])
                await channel.send('みんな今月もいっぱい頑張ったね！みんなの今月の進捗を報告するよ！')
                for user_id in guild_table[2]:
                    cur.execute("SELECT task_ids FROM progress_app.user WHERE id=%s", (user_id, ))
                    task_list = list(cur.fetchone()[0])
                    if len(task_list):
                        sendText = '<@!' + str(user_id) + '>さん'
                        for taskId in task_list:
                            cur.execute("SELECT task_name, duration FROM progress_app.task WHERE id=%s", (taskId, ))
                            task_info = cur.fetchone()
                            sendText = sendText + '\n【作業量】' + str(task_info[0]) + ': ' + str(task_info[1])
                        await channel.send(sendText)
                cur.execute("UPDATE progress_app.guild SET user_ids=%s", ([], ))
            cur.execute("UPDATE progress_app.user SET task_ids=%s", ([], ))
            cur.execute("DELETE FROM progress_app.task")
        conn.commit()
    for data in Data:
        data['start_at'] = datetime.datetime.now().isoformat()
        data['task_id'] = addTask(str(data['user_id']), data['task'])


@client.event
async def on_ready():
    print('sintyokuBot is running')
    while True:
        nowTime = datetime.datetime.now()
        if nowTime.strftime('%d-%H:%M:%S') == '01-00:00:00':
                await reportTheirProgress()
        await asyncio.sleep(60)

@client.event
async def on_voice_state_update(member, before, after):
    if after.channel == None:
        uid = member.id
        for data in Data:
            if data['user_id'] == uid:
                duration = datetime.datetime.now() - datetime.datetime.fromisoformat(data['start_at'])
                await data['channel'].send('<@!' + str(uid) + '>さん\nお疲れ様！頑張ったね！\n【作業量】' + data['task'] +': ' + str(duration))
                addProgressTime(data['task_id'], duration)
                Data.remove(data)
                return

@client.event
async def on_message(message):
    print(message)
    uid = message.author.id
    name = message.author.name
    content = message.content
    guild_id = message.guild.id
    m_channel = message.channel

    if content == '<@!821046992460316733>':
        setNotifyChannel(message.guild, m_channel)

    if message.author.voice == None:
        return

    if re.match(r'^「.+」をやります', content):
        task = content[content.find('「')+1:content.find('」')]
        for data in Data:
            if data['user_id'] == uid:
                if data['task'] == task:
                    await m_channel.send('<@!' + str(uid) + '> さんが「' + task + '」をしてるのちゃんと見てるよ？\n応援してるよ！頑張ってね！')
                    return
                else:
                    await m_channel.send('<@!' + str(uid) + '>さん\n作業を変更するときは一度終了してからもう一度宣言してね！')
                    return
        if not searchGuild(guild_id):
            addGuild(message.guild, uid)
        if not (searchUser(uid) and searchGuildMember(guild_id, uid)):
            addUser(uid, name, guild_id)
        tid = searchTask(uid, task)
        await m_channel.send('<@!' + str(uid) + '> さんは' + task + 'をやるんだね！\n今日も頑張ろう！')
        Data.append({
            'user_id': uid,
            'name': name,
            'start_at': datetime.datetime.now().isoformat(),
            'task': task,
            'task_id': tid,
            'channel': m_channel
        })
    
    if re.match(r'^作業を終わります', content):
        for data in Data:
            if data['user_id'] == uid:
                duration = datetime.datetime.now() - datetime.datetime.fromisoformat(data['start_at'])
                await m_channel.send('<@!' + str(uid) + '>さん\n了解だよ！お疲れ様！\n【作業量】' + data['task'] +': ' + str(duration))
                addProgressTime(data['task_id'], duration)
                Data.remove(data)
                return
        await m_channel.send('<@!' + str(uid) + '>さんはまだ作業開始の宣言をしてないよ？\n何の作業をしてるか教えてね！')

    # if re.match(r'月が変わりました', content):
    #     await reportTheirProgress()

def RunBot():
    try:
        client.run(TOKEN)
    except Exception as e:
        print(e)
        RunBot()

RunBot()