# ベースイメージを選択 (Python 3.9 の軽量版)
FROM python:3.9-slim

# 環境変数: Cloud Runがコンテナに渡すポート番号
# (Streamlitのデフォルトは8501だが、Cloud Runは通常8080を期待)
ENV PORT=8080
# 環境変数: Pythonの出力をバッファリングしない (ログが見やすくなる)
ENV PYTHONUNBUFFERED=1

# 作業ディレクトリを設定・作成
WORKDIR /app

# 依存関係ファイルをコピー
COPY requirements.txt ./

# 依存関係をインストール
# --no-cache-dir: イメージサイズ削減のためキャッシュ無効化
# --upgrade pip: pip自体を最新に更新
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# アプリケーションコードを作業ディレクトリにコピー
# (カレントディレクトリの全ファイルを /app にコピー)
COPY . .

# コンテナがリッスンするポートを公開 (ドキュメント目的 & docker run -P で役立つ)
EXPOSE 8080

# コンテナ起動時に実行されるコマンド
# streamlit run: アプリを起動
# --server.port $PORT: 環境変数PORTで指定されたポートで起動
# --server.headless true: サーバーモードで実行 (ブラウザを開かない)
# --server.enableCORS false / --server.enableXsrfProtection false:
#   Cloud Runのようなプロキシ環境下では不要な場合が多い。
# (元のCMD命令はコメントアウト)
# CMD ["streamlit", "run", "app.py", "--server.port", "${PORT}", "--server.headless", "true", "--server.enableCORS", "false", "--server.enableXsrfProtection", "false"]

# ★★★ Shell形式に変更 ★★★
# シェルが環境変数 $PORT (または ${PORT}) を展開してくれる
CMD streamlit run app.py --server.port ${PORT} --server.headless true --server.enableCORS false --server.enableXsrfProtection false