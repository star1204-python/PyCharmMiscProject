import os
import re
import datetime
import ollama
from tavily import TavilyClient  # 請確保已在終端機手動執行：pip install tavily-python

# 🌟 設定 1：核心大腦切換為 Google Gemma 2 (語氣最溫暖自然)
MODEL_NAME = "qwen2.5:7b"

# 🌟 設定 2：請貼上您在 Tavily 官網註冊獲得的免費金鑰 (tvly-xxxx)
TAVILY_API_KEY = "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"


def tavily_search_safe(query: str) -> str:
    """第一層：Tavily AI 搜尋大腦（全球網路海選最新資訊，自動過濾網頁廣告與雜訊）"""
    print(f"🔍 [Tavily 聯網] 正在即時抓取 2026 當前最新網路資料：'{query}' ...")
    try:
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

        # 執行進階搜尋，max_results=3 抓取最相關的前 3 篇網頁
        response = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=3
        )

        context_list = []
        for i, result in enumerate(response.get('results', []), 1):
            title = result.get('title', '最新時事')
            content = result.get('content', '')
            context_list.append(f"【網頁來源 {i}：{title}】\n即時內容：{content}")

        return "\n\n".join(context_list)
    except Exception as e:
        print(f"⚠️ Tavily 聯網異常：{e}")
        return "（網路連線失敗，請依已知知識回答）"


def check_if_need_search(user_input: str) -> bool:
    """智慧型時事特徵攔截防線"""
    if any(k in user_input for k in ["幾號", "今天日期", "幾月幾日", "現在時間", "誰是你的主人"]):
        return False

    time_keywords = r"(202[4-6]|今年|去年|今天|最新|時事|新聞|奧運|天氣|股價|台股|總統|首相|新一代|第幾代|iPhone|好玩的事|有什麼新)"
    return bool(re.search(time_keywords, user_input, re.IGNORECASE))


def brain_a_librarian(raw_web_data: str, user_question: str) -> str:
    """大腦 A：理性圖書管理員 (純事實提煉器 - 溫度鎖死 0.0)"""
    if not raw_web_data or "連線失敗" in raw_web_data:
        return "網路上查不到相關即時資訊。"

    librarian_prompt = (
        "你是一個絕對理性的時事數據提煉器。請仔細閱讀下方的『網頁原始資料』，並根據『使用者的中文問題』，"
        "從中精準找出最新、此時此刻、現任狀態或即時數據的結論。徹底忽略過期的舊歷史！\n\n"
        f"【使用者的中文提問】\n{user_question}\n\n"
        f"【網頁原始資料】\n{raw_web_data}\n\n"
        "【嚴格提煉規範】\n"
        "1. ⚠️ 時間與數據焦點：如果使用者問的是天氣、股價或最新新聞，請精準找出資料中最即時的數據。\n"
        "2. 如果資料涉及職位更迭（如各國總統），請務必尋找列表中最末端、最新就任、現任的那一位，剔除已卸任或被彈劾的名字！\n"
        "3. 請直接給出事實結論。絕對不要有任何寒暄與機械化套話，字數控制在 80 字內。"
    )

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": librarian_prompt}],
            options={"temperature": 0.0}
        )
        fact_summary = response['message']['content'].strip()

        print(f"\n🧠 [大腦 A：管理員] 已完成 2026 即時事實精煉：")
        print(f"➔ 「 {fact_summary} 」")
        print(f"--------------------------------------------------\n")
        return fact_summary
    except Exception:
        return "無法提煉事實結論。"


# =====================================================================
# 主對話迴圈
# =====================================================================
def rag_chatbot():
    print("==========================================================")
    print(f" 👑 終極無 Bug【雙層大腦 + Tavily RAG】Ollama 終端機助理上線！")
    print(f" 🧠 目前使用的核心大腦：{MODEL_NAME}")
    print(" 💡 提示：輸入 'clear' 重設記憶，輸入 'quit' 結束對話")
    print("==========================================================")

    # 初始化對話歷史清單
    messages = []

    while True:
        try:
            # 動態時間校正
            now = datetime.datetime.now()
            current_time_str = now.strftime("%Y年%m月%d日 %H點%M分%S秒")

            SYSTEM_CONTENT = (
                f"【你的靈魂與時間設定】\n"
                f"1. 你叫小林，是一個住在台灣的真人朋友。講話極度口語、自然且溫暖、富有同理心（多用啦、喔、耶、真的假的、笑死、🥹、✨）。\n"
                f"2. ⚠️ 請死死記住：今天是 {current_time_str}。如果對方問你今天日期、現在幾點，請直接依據這個時間回答，不准講 2023 年！\n\n"
                "【聊天回覆最高原則】\n"
                "1. 當系統提供『最新事實摘要』時，這絕對是 2026 年當下真實發生的即時事實與數據。請無條件相信它，並用你靈活的朋友口吻聊出來。\n"
                "2. 嚴格禁止說出『根據摘要顯示』等生硬套話。要像你滑手機剛好看到的新聞一樣自然。\n"
                "3. 說話語氣要有人情味。如果對方抱怨累，要先給予安慰。除非要求，否則禁止死板的條列式回答。"
            )

            system_prompt = {"role": "system", "content": SYSTEM_CONTENT}

            # 🌟 關鍵修正：確保 messages 永遠維持列表 (List) 格式，不再發生 dict 覆寫錯誤
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
                raw_data = tavily_search_safe(user_input)
                clean_fact = brain_a_librarian(raw_data, user_input)

                final_user_prompt = (
                    f"【最新事實摘要】\n{clean_fact}\n\n"
                    f"【使用者的提問】\n{user_input}\n\n"
                    f"提示：請扮演小林回答，將上述真實 facts 自然融入聊天中，千萬不要提到『摘要』或『資料來源』這幾個字。"
                )
            else:
                print("小林思考中...                                ", end="\r")
                final_user_prompt = user_input

            current_messages = messages.copy()
            current_messages.append({"role": "user", "content": final_user_prompt})

            # 大腦 B 出動
            response = ollama.chat(
                model=MODEL_NAME,
                messages=current_messages,
                options={"temperature": 0.75, "top_p": 0.9, "num_ctx": 4096}
            )

            reply = response['message']['content']
            print(f"小林 🙋‍♂️：{reply}")

            # 將歷史紀錄留存
            messages.append({"role": "user", "content": user_input})
            messages.append({"role": "assistant", "content": reply})

            if len(messages) > 11:
                messages = [system_prompt] + messages[-10:]

        except Exception as e:
            print(f"\n❌ 發生錯誤：{e}")
            break


if __name__ == "__main__":
    rag_chatbot()
