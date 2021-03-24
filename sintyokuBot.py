import discord
import os
import re
import datetime
import psycopg2
from os.path import join, dirname
from dotenv import load_dotenv

load_dotenv(verbose=True)
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

TOKEN = os.environ.get("TOKEN")

client = discord.Client()

Data = []


def searchUser(userId):
    with psycopg2.connect('postgresql://admin:admin@localhost:15432/admin') as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM progress_app.user WHERE id=%s", (userId, ))
            userChecker = cur.fetchone()
            return userChecker
            
def addUser(id, name):
    with psycopg2.connect('postgresql://admin:admin@localhost:15432/admin') as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO progress_app.user VALUES (%s, %s, '{}')", (id, name))
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
    print(duration)
    with psycopg2.connect('postgresql://admin:admin@localhost:15432/admin') as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE progress_app.task SET duration=(duration+%s) WHERE id=%s", (duration, taskId))
        conn.commit()

async def reportTheirProgress(channel):
    with psycopg2.connect('postgresql://admin:admin@localhost:15432/admin') as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, task_ids FROM progress_app.user")
            user_list = cur.fetchall()
            await channel.send('みんな今月もいっぱい頑張ったね！みんなの今月の進捗を報告するよ！')
            for user in user_list:
                sendText = '<@!' + str(user[0]) + '>さん'
                for taskId in user[1]:
                    cur.execute("SELECT task_name, duration FROM progress_app.task WHERE id=%s", (taskId, ))
                    task_info = cur.fetchone()
                    sendText = sendText + '\n【作業量】' + str(task_info[0]) + ': ' + str(task_info[1])
                await channel.send(sendText)
            cur.execute("UPDATE progress_app.user SET task_ids=%s", ([], ))
            cur.execute("DELETE FROM progress_app.task")
        conn.commit()

@client.event
async def on_ready():
    print('sintyokuBot is running')

@client.event
async def on_voice_state_update(member, before, after):
    if after.channel == None:
        uid = member.id
        for data in Data:
            if data['user_id'] == uid:
                duration = datetime.datetime.now() - datetime.datetime.fromisoformat(data['start_at'])
                await data['channel'].send('<@!' + str(uid) + '>さん\nお疲れ様！頑張ったね！\n【作業量】' + data['task'] +': ' + str(duration))
                Data.remove(data)
                return

@client.event
async def on_message(message):
    if message.author.voice == None:
        return
    uid = message.author.id
    name = message.author.name
    content = message.content
    if re.match(r'^「.+」をやります', content):
        task = content[content.find('「')+1:content.find('」')]
        for data in Data:
            if data['user_id'] == uid:
                if data['task'] == task:
                    await message.channel.send('<@!' + str(uid) + '> さんが「' + task + '」をしてるのちゃんと見てるよ？\n応援してるよ！頑張ってね！')
                    return
                else:
                    await message.channel.send('<@!' + str(uid) + '>さん\n作業を変更するときは一度終了してからもう一度宣言してね！')
                    return
        if not searchUser(uid):
            addUser(uid, name)
        tid = searchTask(uid, task)
        await message.channel.send('<@!' + str(uid) + '> さんは' + task + 'をやるんだね！\n今日も頑張ろう！')
        Data.append({
            'user_id': uid,
            'name': name,
            'start_at': datetime.datetime.now().isoformat(),
            'task': task,
            'task_id': tid,
            'channel': message.channel
        })
    
    if re.match(r'^作業を終わります', content):
        for data in Data:
            if data['user_id'] == uid:
                duration = datetime.datetime.now() - datetime.datetime.fromisoformat(data['start_at'])
                await message.channel.send('<@!' + str(uid) + '>さん\n了解だよ！お疲れ様！\n【作業量】' + data['task'] +': ' + str(duration))
                addProgressTime(data['task_id'], duration)
                Data.remove(data)
                return
        await message.channel.send('<@!' + str(uid) + '>さんはまだ作業開始の宣言をしてないよ？\n何の作業をしてるか教えてね！')

    if re.match(r'月が変わりました', content):
        await reportTheirProgress(message.channel)
        
client.run(TOKEN)