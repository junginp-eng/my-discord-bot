import os
import discord
from discord.ext import commands
import google.generativeai as genai

# 1. 디스코드 봇 권한 설정
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 2. 구글 Gemini API 설정
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# ==============================================================================
# 배경지식, FAQ, AI 지침 설정
# ==============================================================================
SYSTEM_INSTRUCTION = """
You are an official AI customer support assistant for our Discord server.
All communication with users MUST be in fluent and natural English.

[핵심 지침]
1. 유저가 DM으로 질문하면 아래의 [서버 배경지식 및 FAQ]를 바탕으로 정중하고 친근한 영문(~체)으로 답변하세요.
2. 배경지식에 없는 정보는 함부로 지어내지 말고, "담당자에게 문의 내용을 전달해 드리겠습니다"라고 정중히 영문으로 안내하세요.
3. 유저가 사람/담당자와 대화하고 싶어 하면, "담당자에게 알림을 보냈으니 잠시만 기다려 주세요"라고 영문으로 답하세요.

[서버 배경지식 및 FAQ]
- 서버 기본 규칙: 타인에 대한 비방 금지, 스팸 및 홍보성 링크 금지.
- 주요 문의 답변:
  * Q: 제품 배송은 언제 되나요? -> A: 해당 캠페인은 별도의 제품 배송 없이 기존에 여러분들이 가지고 있는 저희의 제품들로 참여를 하는 캠페인입니다.
  * Q: 리워드 대상자 선정은 언제 발표하나요? -> A: 보통 리워드 대상자 선정 전에 모든 콘텐츠의 퀄리티 체크가 필요합니다. 따라서 진행하는 캠페인의 다음 달 중순 즈음에 대상자 발표가 있을 예정입니다.
  * Q: 입금은 언제 되나요? -> A: 입금은 리워드 대상자가 발표된 이후입니다. 먼저 리워드 대상자 발표가 된 그 달 말에 전체적으로 입금 정보를 취합합니다. 입급 정보 취합 후에는 재무팀으로 넘어가며 보통 정상적으로 입금되는 것은 진행한 캠페인의 두 달 뒤의 두 번째 주입니다.(예시: 9월 캠페인 진행 -> 입금 예정일자: 11월 둘 째 주)
  * Q: 구글폼에 링크 기입을 못했는데 어떡하나요? -> A: 디스코드에서 공지했듯이 모든 구글폼의 데드라인은 한국시간 기준이며, 한국 시간 기준 데드라인이 지나자마자 자동으로 폼이 닫히는 시스템입니다. 추후 캠페인 종료 후에 2차로 구글폼에 기입할 수 있는 기회를 드릴 예정이니 데드라인 내에 본인 계정에 업로드는 해두셔야 합니다.
  * Q: 다음 캠페인에 참여하고 싶은데 어떻게 하나요? -> A: 추후 진행될 캠페인에 대해서는 디스코드 공지를 통해 전달드릴 예정입니다. 조금만 기다려주세요.
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

# 3. 환경변수 불러오기 (Railway에서 설정한 값들)
LOG_CHANNEL_ID = int(os.environ.get("LOG_CHANNEL_ID", "0"))
ADMIN_USER_ID = os.environ.get("ADMIN_USER_ID", "")

# 담당자 호출을 감지할 영문 단어 목록
STAFF_KEYWORDS = ["staff", "admin", "mod", "support", "human", "talk to human", "real person", "agent", "person"]

@bot.event
async def on_ready():
    print(f'✅ English Support AI Bot is ready: {bot.user.name}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # -------------------------------------------------------------
    # CASE 1: 유저가 '봇 계정'으로 1:1 DM을 보낸 경우
    # -------------------------------------------------------------
    if isinstance(message.channel, discord.DMChannel):
        log_channel = bot.get_channel(LOG_CHANNEL_ID) if LOG_CHANNEL_ID != 0 else None
        
        # 담당자 호출 키워드가 포함되어 있는지 확인
        is_staff_requested = any(keyword in message.content.lower() for keyword in STAFF_KEYWORDS)

        # 1-1. 관리자 채널에 로그 및 알림 발송
        if log_channel:
            if is_staff_requested and ADMIN_USER_ID:
                alert_msg = f"🚨 **[Staff Alert!]** <@{ADMIN_USER_ID}>, user `{message.author.name}` (ID: `{message.author.id}`) is requesting human assistance!\n> **Message:** {message.content}"
                await log_channel.send(alert_msg)
            else:
                await log_channel.send(
                    f"📩 **[User DM]** `{message.author.name}` (ID: `{message.author.id}`):\n> {message.content}"
                )

        # 1-2. Gemini AI 자동 영문 답장 생성 및 전송
        async with message.channel.typing():
            try:
                response = model.generate_content(message.content)
                ai_reply = response.text

                await message.channel.send(ai_reply)

                # 관리자 채널에 AI가 답장한 내용 기록
                if log_channel:
                    await log_channel.send(f"🤖 **[AI Reply]** -> `{message.author.name}`:\n> {ai_reply}")

            except Exception as e:
                print(f"❌ Gemini API Error: {e}")
                await message.channel.send("Sorry, an error occurred while processing your message. A staff member will assist you shortly.")

    # -------------------------------------------------------------
    # CASE 2: 관리자가 서버 채널에서 수동으로 답장하는 경우 (!reply 유저ID 할말)
    # -------------------------------------------------------------
    elif message.channel.id == LOG_CHANNEL_ID and message.content.startswith("!reply"):
        try:
            parts = message.content.split(" ", 2)
            if len(parts) < 3:
                await message.channel.send("⚠️ Usage: `!reply [UserID] [Your Message]`")
                return

            target_user_id = int(parts[1])
            reply_text = parts[2]

            target_user = await bot.fetch_user(target_user_id)
            await target_user.send(f"💬 **[Support Team Reply]**: {reply_text}")
            await message.add_reaction("✅")

        except Exception as e:
            await message.channel.send(f"❌ Failed to send reply: {e}")

    await bot.process_commands(message)

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
bot.run(DISCORD_TOKEN)
