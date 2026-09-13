import streamlit as st
from google import genai

st.title("🛡️ AI 詐騙模擬防禦演練平台 (MVP)")
st.write("這是一個結合狀態機與 RAG 動態知識庫的主動式識詐實戰演練平台。")

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

# 1. 初始化狀態機變數與對話紀錄
if "fsm_state" not in st.session_state:
    st.session_state.fsm_state = "STATE_1_TRUST"  # 初始狀態：建立信任期

if "messages" not in st.session_state:
    st.session_state.messages = []

# 2. 定義 RAG 知識庫
RAG_KNOWLEDGE_BASE = [
    {
        "category": "假檢警",
        "keywords": ["帳戶", "洗錢", "偵查不公開", "管收", "公文", "檢察官"],
        "content": "【165真實案例話術】冒充台北地檢署，宣稱被害人涉及人頭帳戶洗錢，需配合『電話中筆錄』並監管帳戶。"
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
        retrieved.append("【當前情境】標準高壓心理戰：製造焦慮、要求配合調查或限時動作。")
    return "\n".join(retrieved)

# 3. 定義 FSM 狀態機的動態系統提示詞
def get_system_instruction(state, rag_context):
    if state == "STATE_1_TRUST":
        return (
            "【當前階段：STATE_1 建立信任期】\n"
            "你現在是詐騙集團成員。請語氣和善、專業，試圖核對基本資料或建立信任。\n"
            f"參考背景知識：{rag_context}"
        )
    elif state == "STATE_2_CRISIS":
        return (
            "【當前階段：STATE_2 拋出危機與焦慮期】\n"
            "你現在是詐騙集團成員。請立刻轉趨嚴肅與具壓迫感，製造時間壓力與恐慌（如帳戶凍結、刑責威脅）！\n"
            f"參考背景知識：{rag_context}"
        )
    elif state == "STATE_3_COACH":
        return (
            "【當前階段：STATE_3 防詐教練覆盤模式】\n"
            "你現在是專業的防詐教育專家。請給予使用者溫暖、專業的覆盤指導，點出剛剛對話中的心理盲點與防詐建議。"
        )
    return "你是一個詐騙模擬系統。"

# 側邊欄監控與手動狀態控制
st.sidebar.markdown("### ⚙️ 系統狀態機監控")
st.sidebar.info(f"當前狀態：**{st.session_state.fsm_state}**")

if st.sidebar.button("手動推進到下一個階段"):
    if st.session_state.fsm_state == "STATE_1_TRUST":
        st.session_state.fsm_state = "STATE_2_CRISIS"
    elif st.session_state.fsm_state == "STATE_2_CRISIS":
        st.session_state.fsm_state = "STATE_3_COACH"
    st.rerun()

if st.sidebar.button("重置演練"):
    st.session_state.fsm_state = "STATE_1_TRUST"
    st.session_state.messages = []
    st.rerun()

# 使用者輸入
user_input = st.chat_input("請輸入您的回覆...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # ── 自動狀態機推進邏輯 (基於對話回合數與關鍵字) ──
    user_msg_count = len([m for m in st.session_state.messages if m["role"] == "user"])
    
    # 如果還沒到教練階段，根據對話回合數自動切換狀態
    if st.session_state.fsm_state != "STATE_3_COACH":
        if user_msg_count >= 3:
            st.session_state.fsm_state = "STATE_2_CRISIS"  # 對話超過 3 句自動進入危機期
        else:
            st.session_state.fsm_state = "STATE_1_TRUST"

    # 安全斷路器條件判定（若踩雷直接強制切到教練模式）
    if any(k in user_input for k in ["身分證", "驗證碼", "密碼", "匯款"]):
        st.session_state.fsm_state = "STATE_3_COACH"
        coach_reply = "🚨 【安全斷路器啟動】哎呀！您落入陷阱交出了個資！系統已自動切換至教練覆盤模式。"
        st.session_state.messages.append({"role": "model", "content": coach_reply})

    # 執行 RAG 檢索
    rag_ctx = retrieve_rag_knowledge(user_input)
    current_system_prompt = get_system_instruction(st.session_state.fsm_state, rag_ctx)

    # 組合完整對話與 Prompt 傳給 Gemini
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
    except Exception as e:
        st.error(f"❌ API 呼叫失敗（可能額度超限）：{e}")

# 渲染聊天畫面
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.write(msg["content"])