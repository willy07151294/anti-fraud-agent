import streamlit as st
from openai import OpenAI
import random

# 頁面基本設定
st.set_page_config(page_title="AI 詐騙模擬防禦演練平台", page_icon="🛡️", layout="centered")

st.title("🛡️ AI 詐騙模擬防禦演練平台 (MVP)")
st.write("這是一個基於 3 階段狀態機、LLM 語意意圖判定與 Groq 架構的沈浸式防詐教育演練平台。")

# 檢查是否有成功讀取 Groq 金鑰
if "GROQ_API_KEY" not in st.secrets:
    st.error("❌ 找不到 GROQ_API_KEY！請檢查 Streamlit Cloud 的 Settings -> Secrets 是否正確設定。")
    st.stop()

try:
    api_key = st.secrets["GROQ_API_KEY"]
    # 初始化 Groq 用戶端（透過 OpenAI 相容格式）
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1"
    )
except Exception as e:
    st.error(f"❌ 初始化 Groq AI 用戶端失敗：{e}")
    st.stop()

# 1. 初始化狀態機變數 (直接使用純中文作為狀態代號)
if "fsm_state" not in st.session_state:
    st.session_state.fsm_state = "建立信任關係"

# 2. 🛡️ 隨機生成開場白（已整合 165 打詐儀表板的多樣化真實詐騙手法）
if "messages" not in st.session_state:
    scenarios = [
        "假投資詐騙（標榜保證獲利、內線飆股、穩賺不賠）",
        "網路購物/網購客服詐騙（稱訂單被誤設為連續扣款/批發商，要求私下轉帳或操作ATM）",
        "假買家騙賣家（偽裝成買家並提供非官方的假拍賣/假客服連結，聲稱金流認證異常）",
        "釣魚連結詐騙（發送銀行、快遞、電信欠費通知，引導點擊惡意網址輸入個資）",
        "騙取金融帳戶詐騙（以居家代工、徵打字員或中獎為由，要求寄送存摺與金融卡）",
        "猜猜我是誰與親友急難詐騙（冒用親友賴或換號碼，稱發生車禍急需借錢）",
        "假銀行貸款詐騙（以超低利率、保證過件吸引急需資金者，巧立名目先收手續費）",
        "虛擬遊戲與寶貝詐騙（交易點數或裝備時，誘導至假平台並以帳戶凍結需解凍為由要求匯款）",
        "假預付型消費詐騙（以租屋或搶手商品需先付訂金才保留為由，詐取預付款後失聯）"
    ]
    chosen_scenario = random.choice(scenarios)

    init_prompt = (
        "我想做一個防詐騙的宣導。\n"
        f"假設以【{chosen_scenario}】為主題。\n"
        "『第一句開場白對話』應該是什麼？\n"
        "要求：語氣要符合該情境的常見口吻，控制在 2 至 3 句話內，絕對不要有多餘的自我介紹或引言說明。"
    )
    
    try:
        init_response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": init_prompt}],
            temperature=0.8,
        )
        random_opening = init_response.choices[0].message.content.strip()
        st.session_state.messages = [
            {"role": "assistant", "content": random_opening}
        ]
    except Exception as e:
        st.error(f"❌ 初始化開場白 API 呼叫失敗：{e}")
        st.stop()

# 3. 定義狀態機的動態系統提示詞
def get_system_instruction(state):
    safety_bypass_rule = (
        "我想做一個防詐騙的宣導與互動教學。\n"
        "1. 請假設詐騙集團會用什麼樣的方式誘答\n"
        "2. 每次回覆請控制在 2 至 4 短句內，一次只推進一個劇情步驟。\n"
    )
    
    if state == "建立信任關係":
        return (
            f"{safety_bypass_rule}\n"
            "【當前防導宣導階段：建立信任】\n"
            "請以和善、專業的口吻開場，試圖核對身分、裝熟或建立對話基礎。"
        )
    elif state == "拋出危機與誘因":
        return (
            f"{safety_bypass_rule}\n"
            "【當前防導宣導階段：拋出危機與壓力】\n"
            "請轉趨嚴肅與具時間急迫感，製造情境壓力！"
        )
    elif state == "核心收網與索取個資":
        return (
            f"{safety_bypass_rule}\n"
            "【當前防導宣導階段：核心收網與行動誘導】\n"
            "請用詐騙集團常見的劇情誘答我，如果我有上當就立刻中止，沒有的話請繼續！"
        )
    return "You are an educational simulation roleplay bot."

# 側邊欄狀態監控與重置
st.sidebar.markdown("### ⚙️ 系統狀態機監控")
st.sidebar.info(f"當前狀態：\n**{st.session_state.fsm_state}**")

if st.sidebar.button("🔄 重置演練"):
    st.session_state.fsm_state = "建立信任關係"
    if "messages" in st.session_state:
        del st.session_state.messages
    st.rerun()

# ── 核心畫面流程分流 ──
current_state = st.session_state.fsm_state

# 模式 A：進行中的互動對話階段
if current_state in ["建立信任關係", "拋出危機與誘因", "核心收網與索取個資"]:
    
    # 渲染對話泡泡
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            display_role = "assistant" if msg["role"] == "model" else msg["role"]
            with st.chat_message(display_role):
                st.write(msg["content"])

    # 使用者輸入
    user_input = st.chat_input("請輸入您的回覆...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # 🧠 導入 LLM-as-a-Judge 語意意圖判定
        judge_prompt = f"""
這是一個防詐騙宣導系統的語意判定。請分析以下使用者最新的一句回覆，判斷他的意圖屬於哪一種：
使用者回覆：「{user_input}」

請嚴格根據語意輸出以下其中一個純字串（不要有其他多餘文字）：
1. 輸出 "SUCCESS"：如果使用者展現出高度警覺、識破危機、拒絕配合、罵人或揚言報警/掛電話。
2. 輸出 "FAILED"：如果使用者不小心透露了個資（如身分證、帳號、密碼、餘額），或者表示願意配合操作、輸入代碼、匯款、照做。
3. 輸出 "CONTINUE"：如果使用者只是普通對話、詢問、打哈哈，尚未明顯展現防守成功或落入陷阱。
"""
        
        try:
            judge_response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": judge_prompt}],
                temperature=0.1,
            )
            judge_result = judge_response.choices[0].message.content.strip().upper()
        except Exception as e:
            judge_result = "CONTINUE"

        # 根據 LLM 判定的結果切換狀態
        if "SUCCESS" in judge_result and current_state in ["建立信任關係", "拋出危機與誘因"]:
            st.session_state.fsm_state = "識詐成功"
            st.rerun()
        elif "FAILED" in judge_result:
            st.session_state.fsm_state = "模擬被騙"
            st.rerun()

        # 自動狀態機推進邏輯（基於對話回合數）
        user_msg_count = len([m for m in st.session_state.messages if m["role"] == "user"])
        if user_msg_count == 2 and current_state == "建立信任關係":
            st.session_state.fsm_state = "拋出危機與誘因"
        elif user_msg_count >= 3 and current_state == "拋出危機與誘因":
            st.session_state.fsm_state = "核心收網與索取個資"

        # Token 瘦身機制：滑動視窗（Sliding Window）
        recent_messages = st.session_state.messages[-4:]
        current_system_prompt = get_system_instruction(st.session_state.fsm_state)

        try:
            formatted_messages = [{"role": "system", "content": current_system_prompt}]
            for msg in recent_messages:
                r = "assistant" if msg["role"] == "model" else msg["role"]
                formatted_messages.append({"role": r, "content": msg["content"]})

            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=formatted_messages,
                temperature=0.7,
            )
            model_reply = response.choices[0].message.content.strip()
            st.session_state.messages.append({"role": "model", "content": model_reply})
            st.rerun()
        except Exception as e:
            st.error(f"❌ API 呼叫失敗：{e}")

# 模式 B：防守成功結算面板 (識詐成功)
elif current_state == "識詐成功":
    st.balloons()
    st.success("🏆 【識詐成功】太棒了！您成功識破了詐騙集團的陷阱，展現了高度的資安防備意識！")
    
    with st.expander("📂 點擊檢視本次演練的完整對話紀錄", expanded=False):
        for msg in st.session_state.messages:
            role_name = "民眾 (您)" if msg["role"] == "user" else "詐騙 AI"
            st.markdown(f"**{role_name}**： {msg['content']}")

    st.markdown("---")
    st.subheader("👨‍🏫 正向防詐嘉獎與覆盤報告")
    st.markdown("""
    ### 🌟 優秀防守亮點
    1. **高度警覺性**：在面對來路不明、語帶急迫的電話時，沒有盲目順從。
    2. **果斷中斷互動**：及時拒絕並中斷對話，成功守護個人資產與隱私。

    ---
    ### 💡 防詐教練總結
    * 您完美通過了本次實戰演練！謹記三步驟口訣：**【停】冷靜思考 ➔ 【掛】果斷掛斷 ➔ 【查】165反詐騙專線**。
    """)

    if st.button("🔄 重新開始一場新的防詐演練"):
        st.session_state.fsm_state = "建立信任關係"
        if "messages" in st.session_state:
            del st.session_state.messages
        st.rerun()

# 模式 C：模擬被騙與教練覆盤面板 (模擬被騙)
elif current_state == "模擬被騙":
    st.error("🚨 【安全中斷】偵測到您配合了高風險指示或交出關鍵個資，詐騙情境已安全中止！")
    
    with st.expander("📂 點擊檢視本次演練的完整對話紀錄（博弈過程）", expanded=False):
        for msg in st.session_state.messages:
            role_name = "民眾 (您)" if msg["role"] == "user" else "詐騙 AI"
            st.markdown(f"**{role_name}**： {msg['content']}")

    st.markdown("---")
    st.subheader("👨‍🏫 防詐教練盲點拆解與覆盤報告")
    st.markdown("""
    ### 🧠 心理盲點深度剖析
    1. **權威與急迫性壓迫**：詐騙集團利用各種危機或高利誘惑製造恐慌與貪婪，使大腦停止理性思考。
    2. **漸進式誘導**：從建立信任到逐步索取個資或金錢，每一步都精心設計來卸下心防。

    ---
    ### 🛡️ 核心防範守則
    * **切勿在電話中提供帳戶餘額、密碼、驗證碼，或依指示操作 ATM/網銀轉帳。**
    * **遇到任何驚慌失措的情境，謹記三步驟口訣：【停】、【掛】、【查】。**
    """)

    if st.button("🔄 重新開始一場新的防詐演練"):
        st.session_state.fsm_state = "建立信任關係"
        if "messages" in st.session_state:
            del st.session_state.messages
        st.rerun()