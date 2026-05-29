import ollama

MODEL_NAME = "qwen2.5:7b"


def local_chatbot():
    print("==================================================")
    print(f" 🎯 邏輯優化版 Ollama 助理已上線！")
    print(f" 🧠 目前使用的模型：{MODEL_NAME}")
    print(" 💡 提示：輸入 'clear' 可重設記憶，輸入 'quit' 可離開")
    print("==================================================")

    # 🌟 優化 1：重新架構 Prompt，將「事實正確」放在最優先級，再規範語氣
    SYSTEM_CONTENT = (
        "# 核心原則\n"
        "你是一個專業、聰明且說話自然的繁體中文助理。請務必確保回答的事實正確性與邏輯嚴謹度。\n\n"
        "# 回答規範\n"
        "1. 依據事實回答：如果遇到不會或不確定的問題，請直接誠實回答不知道，絕對不可捏造事實或胡言亂語。\n"
        "2. 語氣自然精簡：使用流暢、有人類溫度的台灣繁體中文（如：使用『優化、螢幕、連線』，不使用『優化、屏幕、信號』）。避免生硬的機器人腔調。\n"
        "3. 結構清晰：當使用者詢問複雜問題、技術問題或步驟時，可以適度使用條列式（1. 2. 3.）或區塊來回答，確保易讀性；若是日常閒聊則保持口語化。\n"
        "4. 拒絕贅詞：不要刻意塞滿無意義的口頭禪，只有在語句自然需要時才使用助詞（如：喔、吧）。"
    )

    system_prompt = {"role": "system", "content": SYSTEM_CONTENT}
    messages = [system_prompt]

    while True:
        try:
            user_input = input("\n你 💬：").strip()

            if user_input.lower() == 'quit':
                print("\n助理 🤖：再見！祝你有美好的一天。")
                break

            if user_input.lower() == 'clear':
                messages = [system_prompt]
                print("\n🧹 系統：已重設助理的記憶！")
                continue

            if not user_input:
                continue

            messages.append({"role": "user", "content": user_input})
            print("助理正在思考中...", end="\r")

            # 🌟 優化 2：修正參數！降低 Temperature，拉高 Top_P
            # 這樣可以讓模型變得更加理性、專注於正確答案，並大幅減少胡言亂語
            response = ollama.chat(
                model=MODEL_NAME,
                messages=messages,
                options={
                    "temperature": 0.3,  # 🔴 從 0.85 降到 0.3：大幅降低亂答機率，讓回答專注於邏輯與事實
                    "top_p": 0.9,  # 限制只選擇最合理的詞彙組合
                    "num_ctx": 4096  # 確保上下文記憶視窗足夠，避免因為記憶錯亂導致答案不正確
                }
            )

            reply = response['message']['content']
            print(f"助理 🤖：{reply}")

            messages.append({"role": "assistant", "content": reply})

            if len(messages) > 11:
                messages = [system_prompt] + messages[-10:]

        except Exception as e:
            print(f"\n❌ 發生錯誤：{e}")
            break


if __name__ == "__main__":
    local_chatbot()
