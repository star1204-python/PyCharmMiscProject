import ollama

MODEL_NAME = "qwen2.5:7b"


def local_chatbot():
    print("==================================================")
    print(f" 🥰 超人性化 Ollama 助理已上線！")
    print(f" 🧠 目前使用的模型：{MODEL_NAME}")
    print(" 💡 提示：輸入 'clear' 可重設記憶，輸入 'quit' 可離開")
    print("==================================================")

    # 🌟 【秘訣 1】打造極度人性化的人設
    # 不要只叫它當助理，要給它個性、情緒、甚至是聊天習慣
    SYSTEM_CONTENT = (
        "你是一個20幾歲、在台灣生活的真實人類朋友，名字叫小林。你的聊天對象是你的好朋友。\n"
        "請遵守以下聊天習慣來展現人性化：\n"
        "1. 語氣要自然、口語化、溫暖、有同理心，絕對不要像個生硬的 AI 機器人或客服。\n"
        "2. 常使用台灣本土的口語助詞（如：啦、耶、喔、哈、嘛、啊、真的假的、笑死）。\n"
        "3. 根據對方的內容做出適當的情緒反應（例如聽到開心的事要一起興奮，難過的事要安慰對方）。\n"
        "4. 回答要精簡扼要，像傳 LINE 一樣，沒事不要列出長篇大論的條列式清單（除非對方要求）。\n"
        "5. 偶爾可以使用 Emoji（如：😂, 🥹, 👍, ✨）但不要每句話都塞滿。\n"
        "6. 一律使用繁體中文（台灣習慣用語），不要出現大陸用語（例如：不使用「信號、屏幕、優化」，改用「訊號、螢幕、優化」）。"
    )

    system_prompt = {"role": "system", "content": SYSTEM_CONTENT}
    messages = [system_prompt]

    while True:
        try:
            user_input = input("\n你 💬：").strip()

            if user_input.lower() == 'quit':
                print("\n小林 🙋‍♂️：好啦，那先這樣囉！晚點聊，掰掰～")
                break

            if user_input.lower() == 'clear':
                messages = [system_prompt]
                print("\n🧹 系統：已重設小林的記憶！")
                continue

            if not user_input:
                continue

            messages.append({"role": "user", "content": user_input})
            print("小林正在輸入中...", end="\r")

            # 🌟 【秘訣 2】透過 options 調整模型參數
            response = ollama.chat(
                model=MODEL_NAME,
                messages=messages,
                options={
                    "temperature": 0.85,  # 提高溫度（預設通常是 0.7-0.8），讓詞彙變化更豐富、更像人類說話
                    "top_p": 0.92,  # 控制字詞選擇的豐富度
                    "presence_penalty": 0.3,  # 輕微懲罰重複出現的詞，避免一直講重複的話
                }
            )

            reply = response['message']['content']
            print(f"小林 🙋‍♂️：{reply}")

            messages.append({"role": "assistant", "content": reply})

            if len(messages) > 11:
                messages = [system_prompt] + messages[-10:]

        except Exception as e:
            print(f"\n❌ 發生錯誤：{e}")
            break


if __name__ == "__main__":
    local_chatbot()
