import os
import discord
from discord.ext import commands
from groq import Groq
import datetime
from ddgs import DDGS  # 採用全新官方推薦套件名稱

# ==================== 1. 初始化與設定 ====================
# 🔥 安全提示：請將真正的 Token 填在下方，但切勿再將此程式碼外流！
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "MTUwODgyODY1MjE0MDM2Nzk2Mw.GmJo0T.blrAlnu2yYf64qfwF3YpTfwSNy_6MA5mXbGnZ4")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")

if not GROQ_API_KEY or "你的" in GROQ_API_KEY:
    print("❌ 錯誤：找不到或尚未設定正確的 GROQ_API_KEY。")
    exit()

client = Groq(api_key=GROQ_API_KEY)
today_str = datetime.date.today().strftime("%Y年%m月%d日")

db_history = {}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


def free_web_search(query: str) -> str:
    """
    ✨ 新版 ddgs 專用相容函式：修正參數名稱為 'query'，徹底解決參數缺失報錯
    """
    try:
        # 清除可能誤入的中括號等雜質符號
        search_keyword = query.replace("[", "").replace("]", "").strip()

        # 自動校正關鍵字
        if "總統" in search_keyword and "美" in search_keyword:
            search_keyword = "現任美國總統"

        search_text = f"【以下是透過 DuckDuckGo 為你搜尋到的最新真實網路即時資料】:\n\n"

        with DDGS() as ddgs:
            # 🔥 修正點：將 keywords 參數修改為新版規格的 query 參數
            results = ddgs.text(
                query=search_keyword,
                region="wt-wt",
                safesearch="moderate",
                timelimit="y",
                max_results=4
            )

            # 備用通道：若網頁搜尋無結果，自動改撈新聞庫
            if not results:
                print("💡 備用提示：網頁搜尋空回傳，正在嘗試啟動第二新聞通道...")
                results = ddgs.news(query=search_keyword, region="wt-wt", max_results=3)

                # 終極保險：直接用原始問題再丟一次
            if not results:
                print("💡 終極提示：嘗試使用原始問題檢索...")
                results = ddgs.text(query=query, region="wt-wt", max_results=3)

            if not results:
                return "【網路搜尋提示】：網路檢索連線繁忙，請直接根據常識推論。"

            for idx, re in enumerate(results):
                title = re.get("title", "無標題")
                # text 回傳的欄位是 body，news 回傳的欄位是 snippet
                body = re.get("body", re.get("snippet", "無摘要內容"))
                search_text += f"📢 資料源 {idx + 1}: {title}\n摘要內容: {body}\n\n"

        return search_text
    except Exception as e:
        print(f"⚠️ DuckDuckGo 搜尋發生異常: {e}")
        return "【網路搜尋提示】：外部搜尋引擎連線繁忙，請直接根據已知的常識與邏輯回答。"


# ==================== 2. Discord 事件監聽 ====================
@bot.event
async def on_ready():
    print("==================================================")
    print(f"⚡ 終極黃金完全體機器人 【{bot.user.name}】 已成功上線！")
    print("🎯 聯網引擎已成功升級：相容最新 ddgs 參數規範！")
    print("💡 聯網對話：請在 Discord 輸入「查 + 空格 + 關鍵字」互動！")
    print("==================================================")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    is_search_command = message.content.startswith(('查 ', 'google '))

    if bot.user.mentioned_in(message) or message.attachments or is_search_command or isinstance(message.channel,
                                                                                                discord.DMChannel):

        if message.channel.id not in db_history:
            db_history[message.channel.id] = [
                {"role": "system",
                 "content": f"你是一位在 Discord 服務的專業 AI 助手。請一律使用繁體中文（台灣）回答，並多加點 emoji。記住，今天是 {today_str}，你被賦予了強大的即時聯網搜尋與分析能力，請絕對信任上方提供給你的最新搜尋網頁與摘要，並以此來準確推論並回答使用者。"}
            ]

        history_list = db_history[message.channel.id]

        # 清理使用者輸入文字
        user_text = message.content.replace(f'<@{bot.user.id}>', '').strip()
        if user_text.startswith('查 '):
            user_text = user_text.replace('查 ', '').strip()
        elif user_text.startswith('google '):
            user_text = user_text.replace('google ', '').strip()

        async with message.channel.typing():
            try:
                if message.attachments:
                    await message.reply(
                        "💡 提示：Groq 目前免費版專精於超高速的文字推理與聯網分析喔！如果要聊天請直接輸入文字，或輸入 `查 + 關鍵字` 讓我幫你搜尋網路！")
                    return

                if user_text:
                    # 建立一個臨時要發送給 Groq 的訊息列表，不破壞核心記憶庫
                    messages_to_send = history_list.copy()

                    if is_search_command:
                        print(f"🌐 正在從 DuckDuckGo 檢索關鍵字: {user_text}")
                        realtime_info = free_web_search(user_text)

                        print(f"🔍 DuckDuckGo 成功抓回的內容為:\n{realtime_info}")

                        final_prompt = (
                            f"{realtime_info}\n"
                            f"【系統絕對命令】：上方是幫你從即時網路中檢索到的真實網頁標題與摘要資訊。"
                            f"請你『完全功能性忽視舊記憶，100% 根據上方提供的搜尋內容』，直接、肯定地回答使用者的問題，絕對不能回答不知道或資料過時：\n{user_text}"
                        )
                        history_list.append({"role": "user", "content": f"[網路搜尋] {user_text}"})
                    else:
                        final_prompt = user_text
                        history_list.append({"role": "user", "content": user_text})

                    # 將當前最新的 Prompt 加入要發送給 AI 的臨時列表中
                    messages_to_send.append({"role": "user", "content": final_prompt})

                    # 發送給 Groq API
                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=messages_to_send,
                        temperature=0.3
                    )

                    # 讀取回覆內容
                    ai_reply = response.choices[0].message.content
                    history_list.append({"role": "assistant", "content": ai_reply})

                    if len(ai_reply) > 2000:
                        await message.reply(ai_reply[:1900] + "\n...(字數過長省略)...")
                    else:
                        await message.reply(ai_reply)

            except Exception as e:
                print(f"❌ 發生錯誤: {e}")
                await message.reply(f"❌ 處理訊息時發生錯誤：`{str(e)}`")

            finally:
                if len(history_list) > 7:
                    while len(history_list) > 7:
                        history_list.pop(1)
                print(f"🧠 Python 記憶控管完畢，目前頻道歷史殘留筆數: {len(history_list)}")

    await bot.process_commands(message)


bot.run(DISCORD_TOKEN)
