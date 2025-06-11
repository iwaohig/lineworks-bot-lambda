# LINE WORKS Bot AWS Lambda

LINE WORKS Bot APIを使ったエコー返信ボットのAWS Lambda + API Gateway実装です。

## 🎯 機能

- **✅ エコー返信Bot**: LINE WORKSでメッセージを送信すると「受信しました: [メッセージ]」形式で返信
- **📤 メッセージ送信API**: 外部からREST APIで任意のメッセージを送信
- **🔍 ヘルスチェック**: システム監視用エンドポイント  
- **🧪 テスト機能**: 環境変数設定確認用エンドポイント
- **📥 Webhook受信**: LINE WORKSからのメッセージを正常受信・処理

## 🏗️ AWS構成

```
LINE WORKS ←→ API Gateway ←→ Lambda Function ←→ LINE WORKS API
                    ↓
               CloudWatch Logs
```

## 🌐 デプロイ済みAPI

**ベースURL**: `https://yyjacmzija.execute-api.us-east-1.amazonaws.com/dev/`

| エンドポイント | メソッド | 説明 | ステータス |
|---------------|---------|------|-----------|
| `/health` | GET | ヘルスチェック | ✅ 動作中 |
| `/test` | GET | 環境変数確認 | ✅ 動作中 |
| `/send_message` | POST | メッセージ送信 | ✅ 動作中 |
| `/webhook` | POST | Webhook受信 | ✅ 動作中 |

## 🚀 クイックスタート

### 1. 前提条件

- AWS CLI設定済み
- SAM CLI インストール済み
- LINE WORKS Developer Console アカウント

### 2. 環境変数の設定

以下の環境変数をLambda関数に設定してください（LINE WORKS Developer Consoleから取得）：

```bash
LINEWORKS_CLIENT_ID=your_client_id
LINEWORKS_CLIENT_SECRET=your_client_secret
LINEWORKS_SERVICE_ACCOUNT_ID=your_service_account_id@domain.com
LINEWORKS_PRIVATE_KEY=your_private_key_base64_encoded
LINEWORKS_DOMAIN_ID=your_domain_id
LINEWORKS_BOT_ID=your_bot_id
```

### 3. Webhook URL設定

LINE WORKS Developer Console で以下のWebhook URLを設定：

```
https://yyjacmzija.execute-api.us-east-1.amazonaws.com/dev/webhook
```

### 2. デプロイ手順

#### SAM CLI を使用する場合：

```bash
# パッケージを作成
sam build

# デプロイ
sam deploy --guided
```

#### ZIP デプロイの場合：

```bash
# 依存関係をインストール
pip install -r requirements.txt -t .

# ZIPファイルを作成
zip -r lambda-deployment.zip . -x "*.git*" "__pycache__/*"

# AWS CLI でアップロード
aws lambda update-function-code --function-name your-function-name --zip-file fileb://lambda-deployment.zip
```

### 3. API Gateway設定

以下のエンドポイントを作成：

- `POST /send_message` → Lambda
- `GET /health` → Lambda  
- `GET /test` → Lambda
- `POST /webhook` → Lambda

## 📋 API使用方法

### ✅ ヘルスチェック

```bash
curl "https://yyjacmzija.execute-api.us-east-1.amazonaws.com/dev/health"
```

**レスポンス例:**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-11T21:20:20.780537",
  "version": "1.0.0"
}
```

### 🧪 環境変数テスト

```bash
curl "https://yyjacmzija.execute-api.us-east-1.amazonaws.com/dev/test?name=World"
```

**レスポンス例:**
```json
{
  "message": "Hello, World!",
  "timestamp": "2025-06-11T21:20:24.100671",
  "env_check": {
    "has_client_id": true,
    "has_client_secret": true,
    "has_service_account_id": true,
    "has_private_key": true,
    "has_domain_id": true,
    "has_bot_id": true
  }
}
```

### 📤 メッセージ送信

```bash
curl -X POST "https://yyjacmzija.execute-api.us-east-1.amazonaws.com/dev/send_message" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "target_user_id", 
    "message": "Hello from AWS Lambda!"
  }'
```

**成功レスポンス例:**
```json
{
  "success": true,
  "message": "Message sent successfully",
  "timestamp": "2025-06-11T12:30:45.123456"
}
```

### 📥 エコーBot動作確認

1. LINE WORKSでBotにメッセージを送信: `"Hello"`
2. Botから返信: `"受信しました: Hello"`

## 🎉 実装済み機能

- ✅ **JWT認証**: Service Account認証でLINE WORKS APIにアクセス
- ✅ **エコー返信**: 受信メッセージに対する自動返信
- ✅ **エラーハンドリング**: 秘密鍵パース、JSON解析エラー対応
- ✅ **ログ記録**: CloudWatch Logsで詳細ログ出力
- ✅ **API Gateway**: RESTful API設計

## 必要なLINE WORKS設定

1. **Developer Console でアプリを作成**
   - Bot アプリケーションの作成
   - Service Account認証の設定

2. **認証情報の取得**
   - Client ID
   - Client Secret  
   - Service Account ID（例：xxxxx.serviceaccount@domain.com）
   - Private Key（秘密鍵）

3. **Bot設定**
   - Bot ID: 10207111（設定済み）
   - 必要なScope: bot
   - メッセージ送信権限の確認

4. **ドメイン情報**
   - Domain IDの確認

## 📁 プロジェクト構造

```
lineworks-bot-lambda/
├── README.md                    # プロジェクト説明書
├── requirements.txt             # Python依存パッケージ
├── lambda_function.py           # メインのLambda関数
├── template.yaml               # AWS SAM テンプレート
├── template-simple.yaml        # シンプル版SAMテンプレート
├── .gitignore                  # Git除外設定
├── deployment-guide.md         # デプロイメントガイド
├── quick-deploy-guide.md       # クイックデプロイガイド
└── test-files/
    ├── test-message.json       # メッセージ送信テスト用
    ├── test-payload.json       # Lambda テスト用
    └── webhook-test-message.json # Webhook テスト用
```

## 🔧 技術スタック

- **言語**: Python 3.12
- **フレームワーク**: AWS Lambda
- **インフラ**: AWS SAM (Serverless Application Model)
- **API**: AWS API Gateway
- **認証**: JWT (RS256) + Service Account
- **ログ**: AWS CloudWatch Logs
- **依存パッケージ**: 
  - `PyJWT[cryptography]` - JWT認証
  - `requests` - HTTP通信
  - `cryptography` - 秘密鍵処理

## 📈 将来の拡張予定

- [ ] **コマンド処理**: `/help`, `/weather` 等のコマンド対応
- [ ] **DynamoDB連携**: ユーザーデータ・履歴保存
- [ ] **多言語対応**: 英語・日本語切り替え
- [ ] **リッチメッセージ**: ボタン・カルーセル対応
- [ ] **スケジュール機能**: 定期メッセージ送信
- [ ] **Webhook署名検証**: セキュリティ強化

## 📞 サポート

問題や質問がある場合は、GitHubのIssuesでお気軽にお問い合わせください。

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。