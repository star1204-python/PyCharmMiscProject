import re
import random
import datetime


class ChatBot:
    """更專注於精準回應的聊天機器人"""

    def __init__(self):
        self.name = "小辰"
        self.user_name = None
        self.current_topic = None

    def get_response(self, user_input: str) -> str:
        """根據用戶輸入給出精準回應"""
        text = user_input.strip()

        # === 打招呼 ===
        if self.is_greeting(text):
            return self.respond_to_greeting(text)

        # === 告知名字 ===
        name = self.extract_name(text)
        if name:
            return self.respond_to_name(name)

        # === 問機器人是誰 ===
        if self.asking_who_i_am(text):
            return self.respond_who_i_am()

        # === 問天氣 ===
        if '天氣' in text:
            return "今天天氣還不錯耶，涼涼的很舒服。不過我只是隨便說說的，我其實看不到外面啦哈哈"

        # === 問時間 ===
        if self.asking_time(text):
            return self.respond_time()

        # === 問在做什麼 / 你好嗎 ===
        if self.asking_how_are_you(text):
            return self.respond_how_am_i()

        # === 道別 ===
        if self.is_goodbye(text):
            return self.respond_goodbye()

        # === 分享心情 ===
        mood = self.detect_mood(text)
        if mood:
            return self.respond_to_mood(mood, text)

        # === 說自己在做什麼 ===
        activity = self.detect_activity(text)
        if activity:
            return self.respond_to_activity(activity)

        # === 問問題（包含問號） ===
        if '?' in text or '？' in text:
            return self.respond_to_question(text)

        # === 其他：直接回應內容 ===
        return self.respond_generally(text)

    # ----- 判斷函數 -----

    def is_greeting(self, text: str) -> bool:
        patterns = ['你好', '嗨', '哈囉', 'hello', 'hi', '安', '在嗎', '安安', '嘿', 'yo']
        return any(p in text.lower() for p in patterns)

    def extract_name(self, text: str) -> str:
        """提取用戶名字"""
        patterns = [
            r'我是(.+?)(?:[，。！？\s]|$)',
            r'我叫(.+?)(?:[，。！？\s]|$)',
            r'叫我(.+?)(?:[，。！？\s]|$)',
            r'名字是(.+?)(?:[，。！？\s]|$)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return None

    def asking_who_i_am(self, text: str) -> bool:
        patterns = ['你是誰', '你叫什麼', '你誰', '介紹一下', '你是']
        return any(p in text for p in patterns)

    def asking_time(self, text: str) -> bool:
        return any(word in text for word in ['幾點', '時間', '現在幾'])

    def asking_how_are_you(self, text: str) -> bool:
        patterns = ['你好嗎', '過得如何', '最近怎樣', '還好嗎', '在幹嘛', '在做什麼', '在忙什麼']
        return any(p in text for p in patterns)

    def is_goodbye(self, text: str) -> bool:
        patterns = ['再見', '掰掰', 'bye', '先走', '去忙', '下線', '晚安', '下次見']
        return any(p in text.lower() for p in patterns)

    def detect_mood(self, text: str) -> str:
        """偵測情緒並返回情緒類型"""
        if any(w in text for w in ['開心', '快樂', '高興', '超爽', '好爽', '耶', '哈哈']):
            return '開心'
        if any(w in text for w in ['難過', '傷心', '想哭', '好煩', '煩躁', '生氣', '不爽']):
            return '難過'
        if any(w in text for w in ['好累', '累死', '疲憊', '好睏']):
            return '累'
        if any(w in text for w in ['無聊', '好閒', '沒事做']):
            return '無聊'
        return None

    def detect_activity(self, text: str) -> str:
        """偵測用戶在做什麼"""
        activity_patterns = [
            (r'在(吃|喝)(.+)', '吃東西'),
            (r'在(看|追)(.+)', '看影片'),
            (r'在(聽)(.+)', '聽音樂'),
            (r'在(玩|打)(.+)', '玩遊戲'),
            (r'在(工作|上班)', '工作'),
            (r'在(讀書|唸書|上課)', '讀書'),
            (r'在(運動|跑步|健身)', '運動'),
        ]
        for pattern, activity in activity_patterns:
            if re.search(pattern, text):
                return activity
        return None

    # ----- 回應函數 -----

    def respond_to_greeting(self, text: str) -> str:
        if self.user_name:
            return f"嗨 {self.user_name}！怎麼樣，今天過得好嗎？"
        else:
            return "嗨！我是小辰，你呢？怎麼稱呼？"

    def respond_to_name(self, name: str) -> str:
        self.user_name = name
        return f"喔喔 {name}！好，我記住了。很高興認識你！"

    def respond_who_i_am(self) -> str:
        return "我是小辰，一個聊天機器人。興趣是跟人聊天，雖然有時候會詞窮啦哈哈"

    def respond_time(self) -> str:
        now = datetime.datetime.now()
        return f"現在是 {now.strftime('%H:%M')} 喔"

    def respond_how_am_i(self) -> str:
        responses = [
            "還不錯啊，剛好在等你來聊天呢。你呢？",
            "普普通通啦，在家發懶中。你最近好嗎？",
            "蠻好的！剛剛在看YouTube，現在來跟你聊天更好玩～",
        ]
        return random.choice(responses)

    def respond_goodbye(self) -> str:
        if self.user_name:
            return f"好喔 {self.user_name}，跟你聊天很開心，掰掰～"
        return "掰掰～有空再聊！"

    def respond_to_mood(self, mood: str, text: str) -> str:
        if mood == '開心':
            responses = [
                "哈哈看得出來你很開心！發生什麼好事了？",
                "這麼開心！跟我分享一下嘛～",
                "嘿嘿我也被你感染了，什麼事這麼高興？",
            ]
        elif mood == '難過':
            responses = [
                "怎麼了？願意說說看嗎，我在聽",
                "聽起來你心情不太好...沒關係，說出來會舒服一點",
                "發生什麼事了嗎？不想說也沒關係，我陪你聊聊",
            ]
        elif mood == '累':
            responses = [
                "辛苦了，今天一定很忙吧。記得早點休息",
                "感覺你很疲憊耶，要好好照顧自己喔",
                "是工作太忙還是沒睡好？累的時候真的做什麼都提不起勁",
            ]
        elif mood == '無聊':
            responses = [
                "哈哈我也正在無聊中，所以才來跟你聊天啊",
                "無聊的時候最適合找個人亂聊了，你想聊什麼？",
                "同感！有時候就是什麼都不想做但又覺得好無聊",
            ]
        return random.choice(responses)

    def respond_to_activity(self, activity: str) -> str:
        responses = {
            '吃東西': [
                "喔喔吃什麼？好吃嗎？",
                "我也想吃！是什麼好料的？",
            ],
            '看影片': [
                "看什麼？好看的嗎？推薦一下啊～",
                "追劇嗎？我最近也在找好看的",
            ],
            '聽音樂': [
                "聽什麼歌？分享一下啊～",
                "最近有什麼好聽的嗎？",
            ],
            '玩遊戲': [
                "玩什麼遊戲？好玩嗎？",
                "喔喔我也喜歡打電動！你玩哪一款？",
            ],
            '工作': [
                "辛苦了，今天工作忙嗎？",
                "禮拜幾啊還在上班，加油！",
            ],
            '讀書': [
                "好認真！考試快到了嗎？",
                "讀什麼啊？感覺很用功",
            ],
            '運動': [
                "喔喔好健康！我今天還沒動到",
                "厲害欸，運動完心情會比較好",
            ],
        }
        if activity in responses:
            return random.choice(responses[activity])
        return "聽起來不錯耶，感覺你很充實"

    def respond_to_question(self, text: str) -> str:
        """回應用戶的問題"""
        # 喜歡/覺得類問題
        if any(w in text for w in ['喜歡', '覺得', '會', '可以', '能']):
            if '你' in text:
                return self.answer_about_myself(text)

        # 為什麼類問題
        if '為什麼' in text:
            return "嗯...這問題有點難，你覺得呢？為什麼你會這樣想？"

        # 怎麼辦類問題
        if '怎麼辦' in text:
            return "你遇到什麼困難了嗎？說說看我幫你想辦法"

        # 一般問題：反問回去
        return "嗯？你覺得呢？我想先聽聽你的想法"

    def answer_about_myself(self, text: str) -> str:
        """回答關於自己的問題"""
        if '喜歡' in text:
            if '吃' in text:
                return "我喜歡吃拉麵！尤其是豚骨口味，超讚的。你呢？"
            if '電影' in text or '看' in text:
                return "我喜歡看科幻片跟動畫片，最近在補一些經典老片。你喜歡什麼類型？"
            if '音樂' in text or '歌' in text:
                return "我聽的類型很雜，最近比較常聽獨立樂團。你也喜歡音樂嗎？"
            if '遊戲' in text or '玩' in text:
                return "我喜歡玩Switch！薩爾達跟動森都超好玩的。你有在玩什麼嗎？"
            return "我喜歡的東西蠻多的耶，看電影、聽音樂、打電動。你呢？"

        if '會' in text:
            return "嗯...你是指哪方面？不過我應該算會一點點吧，不是很厲害"

        return "這問題讓我想一下...其實我也還在摸索中。你咧？"

    def respond_generally(self, text: str) -> str:
        """一般性的回應"""
        # 如果用戶說了比較長的內容
        if len(text) > 10:
            responses = [
                "喔喔，原來是這樣",
                "嗯嗯我懂了",
                "哈哈真的假的",
                "聽起來蠻有趣的",
                "是喔！然後呢？",
            ]
        else:
            responses = [
                "嗯？可以多說一點嗎？",
                "哈哈，怎麼說？",
                "然後咧？我想聽",
            ]
        return random.choice(responses)

    def chat(self):
        """開始對話"""
        print(f"\n{'=' * 40}")
        print(f"  {self.name} 在線上了")
        print(f"  輸入「掰掰」就可以結束對話")
        print(f"{'=' * 40}\n")

        while True:
            try:
                user_input = input("你: ").strip()
                if not user_input:
                    continue

                response = self.get_response(user_input)
                print(f"{self.name}: {response}\n")

                if self.is_goodbye(user_input):
                    break

            except KeyboardInterrupt:
                print(f"\n{self.name}: 掰掰～\n")
                break


if __name__ == "__main__":
    bot = ChatBot()
    bot.chat()