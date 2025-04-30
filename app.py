      import streamlit as st
from google.cloud import firestore
import datetime
import pytz
import os
import json

# --- Firestore クライアントの初期化 ---
# GitHub Actions (Cloud Run) ではサービスアカウントキーを使わず認証する想定
# ローカル開発用にサービスアカウントキーJSONを使う場合:
try:
    # Streamlit Secretsから読み込む (ローカル/デプロイ環境共通化のため推奨)
    # .streamlit/secrets.toml に記述:
    # [firestore]
    # key_json = """{ ... }"""
    key_dict = json.loads(st.secrets["firestore"]["key_json"])
    db = firestore.Client.from_service_account_info(key_dict)
except Exception as e1:
    # Streamlit Secretsにない場合、環境変数から読み込む (Cloud Run推奨)
    try:
        key_env_var = os.environ.get("FIRESTORE_CREDENTIALS_JSON")
        if key_env_var:
            key_dict = json.loads(key_env_var)
            db = firestore.Client.from_service_account_info(key_dict)
        else:
            # 環境変数もない場合、デフォルト認証情報 (Cloud Runなど) を試す
            db = firestore.Client()
            st.info("Using default GCP credentials.")
    except Exception as e2:
        st.error(f"Firestore client initialization failed. Secrets Error: {e1}, Default Creds Error: {e2}")
        st.stop()


# --- Streamlit UI 基本設定 ---
st.set_page_config(layout="wide") # ページ幅を広く使う
st.title("Simple Chat App")

# --- チャットルーム選択/ユーザー識別 (仮) ---
# 本来は認証されたユーザー情報を使う
# ここでは仮にユーザー名を直接入力
sender = st.text_input("Your Name (仮)", key="sender_name")
receiver = st.text_input("Partner's Name (仮)", key="receiver_name")

if not sender or not receiver:
    st.warning("Please enter both names.")
    st.stop()

# チャットルームID (単純な例)
room_id = "_".join(sorted([sender, receiver]))
st.subheader(f"Chat Room: {room_id}")

# --- メッセージ表示エリア ---
message_area = st.container()
message_area.height = 400 # 高さを固定してスクロール可能に

def display_messages():
    messages_ref = db.collection("chat_rooms").document(room_id).collection("messages").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(50)
    messages = messages_ref.stream()
    # 逆順で取得しているので表示用にリスト化して反転
    msg_list = list(messages)
    msg_list.reverse()

    with message_area:
        for msg_doc in msg_list:
            msg = msg_doc.to_dict()
            timestamp_jp = msg['timestamp'].astimezone(pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S')
            align = "flex-end" if msg['sender'] == sender else "flex-start" # 簡単な左右寄せ
            st.markdown(f"""

                    **{msg['sender']}** ({timestamp_jp}):
                    {msg['content']}

                """, unsafe_allow_html=True)

# --- メッセージ入力と送信 ---
message_content = st.text_input("Enter message:", key="message_input", value="")
if st.button("Send", key="send_button") and message_content:
    # Firestoreにメッセージを保存
    doc_ref = db.collection("chat_rooms").document(room_id).collection("messages").document()
    doc_ref.set({
        'sender': sender,
        'receiver': receiver, # Firestoreルールで使用するため受信者も保存
        'content': message_content,
        'timestamp': datetime.datetime.now(pytz.utc)
    })
    st.rerun() # 送信後にメッセージリストを再描画

# --- メッセージ表示の実行 ---
display_messages()

# 定期的な更新 (簡易的なポーリング)
# import time
# time.sleep(5)
# st.rerun() # 5秒ごとに再描画 (注意: ユーザー操作を妨げる可能性あり)
# より高度な実装にはWebSocketなどが必要
