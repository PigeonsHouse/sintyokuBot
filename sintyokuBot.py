import discord
import os
import re
import datetime
from os.path import join, dirname
from dotenv import load_dotenv

load_dotenv(verbose=True)
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

TOKEN = os.environ.get("TOKEN")

client = discord.Client()

Data = []

@client.event
async def on_ready():
    print('sintyokuBot is running')

@client.event
async def on_voice_state_update(member, before, after):
    if after.channel == None:
        uid = member.id
        for data in Data:
            if data['userId'] == uid:
                duration = datetime.datetime.now() - datetime.datetime.fromisoformat(data['start_at'])
                await data['channel'].send('<@!' + str(uid) + '>さん\nお疲れ様！頑張ったね！\n【作業量】' + data['task'] +': ' + str(duration))
                Data.remove(data)
                return


@client.event
async def on_message(message):
    if message.author.voice == None:
        return
    username = message.author.name
    uid = message.author.id
    content = message.content
    if re.match(r'^「.*」をやります', content):
        task = content[content.find('「')+1:content.find('」')]

        for data in Data:
            if data['userId'] == uid:
                if data['task'] == task:
                    tmp_start_at = datetime.datetime.fromisoformat(data['start_at'])
                    tmp_duration = datetime.datetime.now() - tmp_start_at
                    await message.channel.send('<@!' + str(uid) + '> さんが作業してるのちゃんと見てるよ？\n応援してるよ！頑張ってね！')
                    return
                else:
                    await message.channel.send('<@!' + str(uid) + '>さん\n作業を変更するときは一度終了してからもう一度宣言してね！')
                    return
        await message.channel.send('<@!' + str(uid) + '> さんは' + task + 'をやるんだね！\n今日も頑張ろう！')
        Data.append({
            'userId': uid,
            'userName': username,
            'start_at': datetime.datetime.now().isoformat(),
            'task': task,
            'channel': message.channel
        })
    
    if re.match(r'^作業を終わります', content):
        for data in Data:
            if data['userId'] == uid:
                duration = datetime.datetime.now() - datetime.datetime.fromisoformat(data['start_at'])
                await message.channel.send('<@!' + str(uid) + '>さん\n了解だよ！お疲れ様！\n【作業量】' + data['task'] +': ' + str(duration))
                Data.remove(data)
                return
        await message.channel.send('<@!' + str(uid) + '>さんはまだ作業開始の宣言をしてないよ？\n何の作業をしてるか教えてね！')

    if re.match(r'作業量を教えて', content):
        for data in Data:
            if data['userId'] == message.author.id:
                tmp_duration = datetime.datetime.now() - datetime.datetime.fromisoformat(data['start_at'])
                await message.channel.send('<@!' + str(uid) + '>さん\n了解だよ！頑張ってるね！\n【作業量】' + data['task'] +': ' + str(tmp_duration))
                return
        await message.channel.send('<@!' + str(uid) + '>さんはまだ作業開始の宣言をしてないよ？\n何の作業をしてるか教えてね！')
        
client.run(TOKEN)