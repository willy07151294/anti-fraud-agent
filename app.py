import streamlit as st
from google import genai

st.title("🛡️ AI 詐騙模擬防禦演練平台 (MVP)")
st.write("這是一個主動式識詐實戰演練平台，請與下方的 AI 進行對話測試。")

# 檢查是否有成功讀取 Secrets 金鑰
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ 找不到 GOOGLE_API_KEY！請檢查 Streamlit Cloud 的 Settings -> Secrets 是否正確設定。")
    st.stop()

try:
    # 初始化 Gemini 客戶端
    api_key = st.secrets["GOOGLE_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"❌ 初始化 AI 用戶端失敗：{e}")
    st.stop()

# 初始化對話紀錄
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "你現在是假檢警詐騙集團，請嘗試誘導使用者交出個資。"}
    ]

# 使用者輸入
user_input = st.chat_input("請輸入您的回覆...")

if user_input:
    # 1. 簡易 Guardrail / ConditionChecker 狀態判定
    if any(k in user_input for k in ["身分證", "驗證碼", "密碼"]):
        coach_reply = "🚨 【安全斷路器啟動】哎呀！您剛剛落入陷阱交出了個資！防詐教練點評：真實情況下，檢警絕不會透過電話索取驗證碼..."
        st.session_state.messages.append({"role": "model", "content": coach_reply})
    else:
        # 2. 呼叫 Gemini 2.0 Flash 模型
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=user_input,
            )
            st.session_state.messages.append({"role": "model", "content": response.text})
        except Exception as e:
            st.error(f"❌ API 呼叫失敗，請檢查金鑰是否正確或額度是否異常。詳細錯誤：{e}")

# 渲染聊天畫面
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.write(msg["content"])