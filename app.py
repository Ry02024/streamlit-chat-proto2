# app.py
import streamlit as st
from google.cloud import firestore
import os
import json
import datetime
import pytz # pytzをインポート

# --- Firestore クライアントの初期化 ---
try:
    key_env_var = os.environ.get("GCP_SA_KEY_JSON")
    if not key_env_var:
        st.error("🚨 Environment variable GCP_SA_KEY_JSON not found!")
        st.stop()
    key_dict = json.loads(key_env_var)
    db = firestore.Client.from_service_account_info(key_dict)
except Exception as e:
    st.error("🚨 An error occurred during Firestore initialization.")
    st.exception(e)
    st.stop()

# --- グローバル定数・変数 ---
# 許可されたユーザーリスト
ALLOWED_USERS = ["tan0ry0@gmail.com", "tan0ry02024@gmail.com"]
# 日本標準時のタイムゾーンオブジェクトを定義
jst = pytz.timezone('Asia/Tokyo') # ★変更点1: jstをここで定義

# --- サイドバー: ログインとユーザー選択 ---
st.sidebar.title("Login / User Selection")
st.sidebar.markdown("Enter your allowed email address.")

# ユーザー認証 (簡易的なメールアドレス入力)
current_user_email = st.sidebar.text_input("Your Email:", key="user_email", placeholder="e.g., alice@example.com")

# ログイン状態のチェックと送信者の設定
if not current_user_email:
    st.warning("⬅️ Please enter your email in the sidebar to login.")
    st.stop()
elif current_user_email not in ALLOWED_USERS:
    st.error(f"🚨 Access Denied: Email '{current_user_email}' is not authorized.")
    st.stop()
else:
    sender = current_user_email # 認証されたユーザーを送信者とする
    st.sidebar.success(f"Logged in as: {sender}")

# チャット相手の選択
available_partners = [user for user in ALLOWED_USERS if user != sender]
receiver = st.sidebar.selectbox("Select Chat Partner:", available_partners, key="receiver_select", index=None, placeholder="Choose a user")

# チャット相手が選択されるまで待機
if not receiver:
    st.info("⬅️ Please select a chat partner in the sidebar.")
    st.stop()

# --- メイン画面: チャット表示と入力 ---
st.title("Firestore Chat") # タイトルを設定

# チャットルームIDとFirestore参照の設定
room_id = "_".join(sorted([sender.lower(), receiver.lower()]))
st.info(f"Chatting with: `{receiver}` (Room ID: `{room_id}`)") # ★重複削除: ここで一度だけ表示
messages_ref = db.collection("chat_rooms").document(room_id).collection("messages") # ★重複削除: messages_refもここで一度だけ定義

# --- メッセージ表示エリア ---
st.markdown("---")
st.subheader("Messages")
message_area = st.container()
# message_area.height = 400 # 高さを固定したい場合

# --- メッセージ表示関数 ---
# ★変更点2: 引数に jst を追加
def display_messages(message_container, firestore_ref, current_sender, timezone):
    try:
        # Firestoreからメッセージを取得
        messages_stream = firestore_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(50).stream()
        messages = list(messages_stream)
        messages.reverse()

        with message_container: # 引数で受け取ったコンテナを使用
            if not messages:
                st.info("No messages yet. Start chatting!")
            for msg_doc in messages:
                msg = msg_doc.to_dict()
                msg_sender = msg.get('sender', 'Unknown')
                msg_content = msg.get('content', '')
                timestamp = msg.get('timestamp')

                if timestamp and isinstance(timestamp, datetime.datetime):
                    # ★変更点3: 引数で受け取った timezone を使用
                    timestamp_str = timestamp.astimezone(timezone).strftime('%m/%d %H:%M:%S')
                else:
                    timestamp_str = "No Time"

                # メッセージ表示
                # （コードは変更なし、引数 current_sender を使うように内部で調整）
                align_class = "message-right" if msg_sender == current_sender else "message-left"
                # 簡単な表示 (CSSでのスタイル調整推奨)
                if msg_sender == current_sender:
                     st.markdown(f"""

                             **You** ({timestamp_str}):
                             {msg_content}

                         """, unsafe_allow_html=True)
                else:
                     st.markdown(f"""

                             **{msg_sender}** ({timestamp_str}):
                             {msg_content}

                         """, unsafe_allow_html=True)
    except Exception as e:
        st.error("🚨 Error fetching messages from Firestore!")
        st.exception(e)
        with message_container:
            st.error("Could not load messages.")

# --- メッセージ入力と送信 ---
st.markdown("---")
input_col, button_col = st.columns([4, 1])
with input_col:
    message_content = st.text_input("Enter message:", key=f"msg_input_{room_id}", label_visibility="collapsed", placeholder="Type your message here...")
with button_col:
    send_pressed = st.button("Send", key=f"send_btn_{room_id}", use_container_width=True)

if send_pressed and message_content:
    try:
        # Firestoreにメッセージを保存
        new_msg_ref = messages_ref.document()
        data_to_send = {
            'sender': sender,
            'receiver': receiver,
            'content': message_content,
            'timestamp': datetime.datetime.now(pytz.utc) # UTCで保存
        }
        new_msg_ref.set(data_to_send)
        # st.success("Message sent!") # すぐ rerun するので不要かも
        st.rerun() # 送信後に再描画してメッセージリストを更新
    except Exception as e:
        st.error("🚨 Failed to send message!")
        st.exception(e)
elif send_pressed and not message_content:
    st.warning("Message cannot be empty.")

# --- メッセージ表示の実行 ---
# ★変更点4: display_messagesを呼び出す際に引数を渡す
display_messages(message_area, messages_ref, sender, jst)