import streamlit as st
from google import genai

# 頁面基本設定
st.set_page_config(page_title="AI 詐騙模擬防禦演練平台", page_icon="🛡️", layout="centered")

st.title("🛡️ AI 詐騙模擬防禦演練平台 (MVP)")
st.write("這是一個結合動態心理戰術與防詐教練覆盤的沈浸式實戰演練環境。")

# 檢查是否有成功讀取 Secrets 金鑰
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ 找不到 GOOGLE_API_KEY！請檢查 Streamlit Cloud 的 Settings -> Secrets 是否正確設定。")
    st.stop()

try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"❌ 初始化 AI 用戶端失敗：{e}")
    st.stop()

# 1. 初始化狀態機變數
if "fsm_state" not in st.session_state:
    st.session_state.fsm_state = "STATE_1_TRUST"  # 初始狀態：建立信任期

# 2. 定義 RAG 知識庫
RAG_KNOWLEDGE_BASE = [
    {
        "category": "假檢警",
        "keywords": ["帳戶", "洗錢", "偵查不公開", "管收", "公文", "檢察官", "身分證", "出生年月日"],
        "content": "【165真實案例話術】冒充台北地檢署或金融機構，宣稱涉及人頭帳戶洗錢，需配合電話中筆錄並進行身分核對與資金監管。"
    },
    {
        "category": "假投資",
        "keywords": ["飆股", "內線", "群組", "老師", "高報酬", "抽籤", "投資"],
        "content": "【165真實案例話術】透過社群引導加入投資群組，聲稱內線保證獲利，誘騙民眾大額入金。"
    },
    {
        "category": "假網購",
        "keywords": ["分期付款", "ATM", "操作", "客服", "重複扣款"],
        "content": "【165真實案例話術】假冒網購客服，稱工作人員疏失設成連續扣款，需至 ATM 或網銀解除設定。"
    }
]

def retrieve_rag_knowledge(user_message):
    retrieved = []
    for item in RAG_KNOWLEDGE_BASE:
        if any(kw in user_message for kw in item["keywords"]):
            retrieved.append(item["content"])
    if not retrieved:
        retrieved.append("【當前情境】標準心理戰：語氣從容且帶有引導性，逐步建立情境壓力。")
    return "\n".join(retrieved)

# 3. 定義 FSM 狀態機與對話節奏約束
def get_system_instruction(state, rag_context):
    pacing_rule = (
        "【重要對話互動原則】：\n"
        "1. 請模擬真實人類在電話或通訊軟體中的說話方式，絕對不要長篇大論。\n"
        "2. 每次回覆控制在 2 至 4 短句內就好，一次只丟出一個問題或一個步驟，像真人一樣步步為營。\n"
    )
    
    if state == "STATE_1_TRUST":
        return (
            "【當前階段：STATE_1 建立信任期】\n"
            f"{pacing_rule}"
            "你現在是詐騙集團成員（例如網購客服或銀行專員）。請主動撥通電話並以和善語氣開場，試圖核對基本資料或建立信任。\n"
            f"參考背景知識：{rag_context}"
        )
    elif state == "STATE_2_CRISIS":
        return (
            "【當前階段：STATE_2 拋出危機與焦慮期】\n"
            f"{pacing_rule}"
            "你現在是詐騙集團成員。請開始帶入危機感，語氣轉為急促、專業但具壓迫感！\n"
            f"參考背景知識：{rag_context}"
        )
    return "你是一個詐騙模擬系統。"

# ── 嚴格防呆的初始化：確保 AI 開場白只會在剛進網頁或重置時呼叫一次 ──
if "messages" not in st.session_state:
    st.session_state.messages = []
    initial_prompt = get_system_instruction("STATE_1_TRUST", "【情境】假冒網購客服來電，指稱發生重複扣款需協助解除。")
    try:
        init_response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=f"{initial_prompt}\n\n請直接撥通電話並說出你的第一句開場白（例如假裝是客服人員打來）。",
        )
        st.session_state.messages.append({"role": "model", "content": init_response.text})
    except Exception as e:
        st.session_state.messages.append({"role": "model", "content": "喂您好，這裡是某某網購客服中心，不好意思深夜打擾您，我們系統顯示您的訂單被設成了連續扣款..."})

# 側邊欄監控與手動狀態控制
st.sidebar.markdown("### ⚙️ 系統狀態機監控")
st.sidebar.info(f"當前狀態：**{st.session_state.fsm_state}**")

if st.sidebar.button("強制推進到下一個戰術階段"):
    if st.session_state.fsm_state == "STATE_1_TRUST":
        st.session_state.fsm_state = "STATE_2_CRISIS"
    elif st.session_state.fsm_state == "STATE_2_CRISIS":
        st.session_state.fsm_state = "STATE_3_COACH"
    st.rerun()

if st.sidebar.button("重置演練 (重新接聽電話)"):
    st.session_state.fsm_state = "STATE_1_TRUST"
    st.session_state.messages = []
    st.rerun()

# ── UI 介面呈現邏輯：區隔「沈浸式對話」與「教練覆盤面板」──

if st.session_state.fsm_state != "STATE_3_COACH":
    # 正常對話階段：渲染聊天介面
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    # 使用者輸入
    user_input = st.chat_input("請輸入您的回覆...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # 條件判定與安全斷路器 (ConditionChecker) - 包含身分證、密碼、匯款、特定代號等
        if any(k in user_input for k in ["身分證", "驗證碼", "密碼", "匯款", "A125865925", "88591"]):
            st.session_state.fsm_state = "STATE_3_COACH"
            st.rerun()

        # 執行 RAG 檢索與系統提示詞組合
        rag_ctx = retrieve_rag_knowledge(user_input)
        current_system_prompt = get_system_instruction(st.session_state.fsm_state, rag_ctx)

        try:
            full_contents = f"{current_system_prompt}\n\n"
            for msg in st.session_state.messages:
                role_label = "使用者" if msg["role"] == "user" else "AI"
                full_contents += f"{role_label}：{msg['content']}\n"

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=full_contents,
            )
            st.session_state.messages.append({"role": "model", "content": response.text})
            st.rerun()
        except Exception as e:
            st.error(f"❌ API 呼叫失敗或額度超限 (429)：請稍候 30 秒再試。詳細錯誤：{e}")

else:
    # 🚨 狀態 3：安全斷路器啟動，進入獨立的「防詐教練結算面板」
    st.error("🚨 【安全斷路器啟動】偵測到配合詐騙指示或個資外洩，詐騙情境已安全中止！")
    
    with st.expander("📂 點擊檢視本次演練的完整對話紀錄（博弈過程）", expanded=False):
        for msg in st.session_state.messages:
            role_name = "民眾 (您)" if msg["role"] == "user" else "詐騙 AI"
            st.markdown(f"**{role_name}**： {msg['content']}")

    st.markdown("---")
    st.subheader("👨‍🏫 防詐教練深度覆盤與盲點拆解報告")
    
    st.markdown("""
    ### 🧠 心理盲點深度剖析
    1. **漸進式誘導與代號配合**：
       * 詐騙集團透過引導您準備卡片、抄寫解除代號（如 88591）並準備接聽下一通電話，讓您在沒有交出密碼的情況下，依然落入誘導操作的陷阱。
    2. **製造焦慮與急迫感**：
       * 宣稱今晚會自動扣款，強迫大腦進入緊急應變狀態，因而降低了對來電真實性的懷疑。
    3. **轉接手法（二次詐騙）**：
       * 利用「轉接給銀行專員」的說法，降低民眾對第一通電話的戒心。

    ---
    ### 🛡️ 核心防範守則
    * **金融機構絕不會要求您抄寫代號並轉接給其他專員操作 ATM 或網銀。**
    * **遇到任何驚慌失措的情境，謹記三步驟口訣：【停】冷靜思考 ➔ 【掛】果斷掛斷 ➔ 【查】自行撥打官方或 165 專線查證。**
    """)

    if st.button("🔄 重新開始一場新的防詐演練"):
        st.session_state.fsm_state = "STATE_1_TRUST"
        st.session_state.messages = []
        st.rerun()