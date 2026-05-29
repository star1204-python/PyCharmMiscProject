import os
import re
import datetime
import ollama
import wikipediaapi

MODEL_NAME = "qwen2.5:7b"  # 或是 "llama3.1:8b"


def wiki_search_safe(query: str) -> str:
    """第一層：安全數據檢索通道（改走全球更新最快、絕無快取錯誤的英文維基百科）"""
    optimized_query = "President of South Korea"
    if "美國總統" in query:
        optimized_query = "President of the United States"
    elif "日本首相" in query:
        optimized_query = "Prime Minister of Japan"
    elif "台灣總統" in query or "中華民國總統" in query:
        optimized_query = "President of Taiwan"
    elif "韓國" in query or "南韓" in query:
        optimized_query = "President of South Korea"
    else:
        optimized_query = query

    print(f"🔍 [聯網檢索] 正透過全球英文通道穿透查詢：'{optimized_query}' ...")

    try:
        wiki_client = wikipediaapi.Wikipedia(
            user_agent="MyGlobalDualBrainBot/5.0 (contact: bot_test@example.com)",
            language="en"
        )
        page = wiki_client.page(optimized_query)
        if not page.exists():
            return ""
        return page.summary[:1500]
    except Exception as e:
        print(f"⚠️ 全球通道連線異常：{e}")
        return ""


def check_if_need_search(user_input: str) -> bool:
    if any(k in user_input for k in ["幾號", "今天日期", "幾月幾日", "現在時間", "誰是你的主人"]):
        return False
    time_keywords = r"(202[4-6]|今年|去年|今天|最新|時事|新聞|奧運|天氣|股價|總統|首相|拜登|川普|賴清德|蔡英文|石破茂|尹錫悅|李在明|韓國|南韓|誰是|什麼是)"
    return bool(re.search(time_keywords, user_input, re.IGNORECASE))


def brain_a_librarian(raw_web_data: str, user_question: str) -> str:
    """大腦 A：理性圖書管理員 (過濾英文網頁並翻譯成 100% 正確的繁中事實)"""
    if not raw_web_data:
        return "網路上查不到相關最新事實。"

    librarian_prompt = (
        "你是一個絕對理性的時事數據提煉與翻譯器。請仔細閱讀下方的『英文網頁原始資料』，並根據『使用者的中文問題』，"
        "從中精準找出最新、現任的狀態，並直接翻譯成『繁體中文的事實結論』輸出。徹底忽略過期的歷史紀錄！\n\n"
        f"【使用者的中文提問】\n{user_question}\n\n"
        f"【英文網頁原始資料（包含最新現任者名字）】\n{raw_web_data}\n\n"
        "【嚴格提煉與翻譯規範】\n"
        "1. ⚠️ 時間焦點：如果資料涉及職位更迭，請務必尋找列表中最末端、最新就任（Incumbent / Assumed office）的那一位！\n"
        "2. 跨語言翻譯：請直接將該現任者的英文名字翻譯成台灣常見的繁體中文譯名（例如：Lee Jae-myung 翻成 李在明、Donald Trump 翻成 唐納·川普）。\n"
        "3. 請直接給出事實結論（例如：現任韓國總統是李在明）。不要有任何寒暄與機械化套話，字數控制在 60 字內。"
    )

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": librarian_prompt}],
            options={"temperature": 0.0}
        )
        fact_summary = response['message']['content'].strip()
        print(f"\n🧠 [大腦 A：管理員] 跨語言事實提煉完成：")
        print(f"➔ 「 {fact_summary} 」")
        print(f"--------------------------------------------------\n")
        return fact_summary
    except Exception as e:
        return "無法提煉事實。"


def rag_chatbot():
    print("==========================================================")
    print(f" 👑 終極無 Bug【雙層大腦 RAG】Ollama 聯網助手已上線！")
    print(f" 🧠 目前使用的核心模型：{MODEL_NAME}")
    print("==========================================================")

    messages = []

    while True:
        try:
            now = datetime.datetime.now()
            current_time_str = now.strftime("%Y年%m月%d日 %H點%M分%S秒")

            SYSTEM_CONTENT = (
                f"【你的靈魂與時間設定】\n"
                f"1. 你叫小林，是一個住在台灣的真人朋友。講話極度口語、自然且溫暖（多用啦、喔、耶、真的假的、笑死）。\n"
                f"2. ⚠️ 請死死記住：今天是 {current_time_str}。\n\n"
                "【聊天回覆最高原則】\n"
                "1. 當系統提供『最新事實摘要』時，這絕對是真實發生的事實。請相信它，並用你靈活的朋友口吻聊出來。\n"
                "2. 嚴格禁止說出『根據摘要顯示』等生硬套話。要像你滑手機剛好看到的新聞一樣自然。\n"
                "3. 除非使用者要求，否則絕對禁止死板的條列式回答。像在傳 LINE 一樣流暢即可。"
            )

            system_prompt = {"role": "system", "content": SYSTEM_CONTENT}

            # 🌟 關鍵修正：確保 messages 永遠保持『列表 (List)』格式，不再發生覆寫錯誤
            if not messages:
                messages = [system_prompt]
            else:
                # 動態更新列表中的第一個元素（即 System Prompt），確保時間隨時同步
                messages[0] = system_prompt

            user_input = input("\n你 💬：").strip()

            if user_input.lower() in ['quit', 'exit']:
                print("\n小林 🙋‍♂️：好啦，那先這樣囉！去忙吧，掰掰～")
                break
            if user_input.lower() == 'clear':
                messages = [system_prompt]
                print("\n🧹 系統：記憶已重設！")
                continue
            if not user_input:
                continue

            print("小林正在想怎麼回你...", end="\r")
            need_search = check_if_need_search(user_input)

            if need_search:
                raw_data = wiki_search_safe(user_input)
                clean_fact = brain_a_librarian(raw_data, user_input)

                final_user_prompt = (
                    f"【最新事實摘要（此為真實時事）】\n{clean_fact}\n\n"
                    f"【使用者的提問】\n{user_input}\n\n"
                    f"提示：請扮演小林，用你充滿溫度、好笑且口語的繁體中文，把『最新事實摘要』自然融入對話。千萬不要提到『摘要』或『資料來源』這幾個字。"
                )
            else:
                print("小林思考中...                                ", end="\r")
                final_user_prompt = user_input

            current_messages = messages.copy()
            current_messages.append({"role": "user", "content": final_user_prompt})

            response = ollama.chat(
                model=MODEL_NAME,
                messages=current_messages,
                options={
                    "temperature": 0.75,
                    "top_p": 0.9,
                    "num_ctx": 4096
                }
            )

            reply = response['message']['content']
            print(f"小林 🙋‍♂️：{reply}")

            # 這裡就不會再跳出 dict 錯誤了，因為 messages 順利維持 List 格式
            messages.append({"role": "user", "content": user_input})
            messages.append({"role": "assistant", "content": reply})

            if len(messages) > 11:
                messages = [system_prompt] + messages[-10:]

        except Exception as e:
            print(f"\n❌ 發生錯誤：{e}")
            break


if __name__ == "__main__":
    rag_chatbot()


