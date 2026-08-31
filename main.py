import os
import discord
from discord.ext import commands

# 봇 권한 설정
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 1. 전송할 이미지 URL 입력 (디스코드 채널에 올린 후 우클릭 -> 이미지 주소 복사한 링크)
IMAGE_URL = "https://cdn.discordapp.com/attachments/1543799994178469993/1543807592659427439/0a810b6b1dc992fc.png?ex=6a96365c&is=6a94e4dc&hm=66ca27cdb0d7d2f5c2ec896c8b332dc861e4c5b13df74e0937ca2023762eb259&"

@bot.event
async def on_ready():
    print(f'✅ 봇이 정상적으로 로그인되었습니다: {bot.user.name}')

@bot.event
async def on_message(message):
    # 봇 자신의 메시지에는 반응하지 않음 (무한루프 방지)
    if message.author == bot.user:
        return

    # 유저가 '봇 계정'으로 1:1 개인 메시지(DM)를 보낸 경우
    if isinstance(message.channel, discord.DMChannel):
        embed = discord.Embed(
            title="📌 Inquiries & Customer Service",
            description="Hello! Please check the image below. If that still doesn't resolve the issue, please send a 1:1 DM to the official Abib account.",
            color=0x3498db
        )
        # 이미지 첨부
        embed.set_image(url=IMAGE_URL)
        
        # 유저에게 자동 답장 전송
        await message.channel.send(embed=embed)

# 2. 토큰값은 클라우드 환경변수(DISCORD_TOKEN)에서 안전하게 불러옵니다.
TOKEN = os.environ.get("DISCORD_TOKEN")
bot.run(TOKEN)