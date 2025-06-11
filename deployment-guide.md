# LINE WORKS Bot Azure Functions デプロイガイド

## 方法1: Azure ポータル経由（推奨）

### Step 1: Azure ポータルでFunction App作成

1. [Azure ポータル](https://portal.azure.com) にログイン
2. 「リソースの作成」→「Function App」を選択
3. 基本設定：
   - **Function App名**: lineworks-bot-functions（またはユニークな名前）
   - **ランタイムスタック**: Python 3.11
   - **バージョン**: 3.11
   - **リージョン**: Japan East
   - **オペレーティングシステム**: Linux

### Step 2: 環境変数の設定

Function App作成後、「構成」→「アプリケーション設定」で以下を追加：

```
LINEWORKS_CLIENT_ID = MhOIRuvy6pmxUcNTAxTg
LINEWORKS_CLIENT_SECRET = VjlkX_IIxs
LINEWORKS_SERVICE_ACCOUNT_ID = wpumx.serviceaccount@lwugdev
LINEWORKS_DOMAIN_ID = 400083023
LINEWORKS_BOT_ID = 10207111
LINEWORKS_PRIVATE_KEY = -----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDX8rP8DhnTJw6n
HPIjLhUx6mVjGXTqYTJMNzbGIaxuWOvS9CixBYmB7oXWvp1mhHlhLYmskKWiC5/1
RzcN1/4dxc+A2NuvXLbRU0g2p4TOT6UWz9J9BfDvlLV5hDh1xjpmveOdWjKTQQ7+
fKJyA5mzfh2HDNzPZhKo+lZqYDkCgzPawQUFR/VPydEaGBrNkoclQdjvvqI8AjpU
RxsACd5/SkS5D5al09QJQwkt2z9pN2K6l3pJbfBfAcsDsbvlFxz9j3Jcae+puJ8E
0DePVbSncflppwk4QxIUk6dCPjLXlUyzY0sfAyL22Vm1o4ZK79jGVMjBmegVn6+D
LfwyiNk7AgMBAAECggEAZC+oiwbrukfDh4ppWCL4GFlbwlc8I8UGNc/j7JYQzn0Y
o509B6u++PX1SATVN4u8WHZtCg9tmLl187CffR+5OIzeUTPK8Be+hWzy8tBTT/gp
amTujaxk9HH0o7TREOrvi10LraP8FM85Kp4eK3E6LMkU3+P6yYncnGLQFrgfmubz
qhZDFu1KUf9Aw015vzq/1yZW1eVQzRQfg/10ibdLGtPmsPXFWmwlaAd5eV/gbfrU
cTDwTGyu5YDQzc5McDpslB9Kl4abC3nJRqqvlVRLDrXSWeW+TZ+qrGT3mKLelTFs
VG7Rho6o+0svdFBVSV70uS6J4E4kbOOb/QagCEtnWQKBgQDzdDcCERN+BMQWMbUc
hEC/abOxUh3/Psh5jstTsdrWT6q32Ylzk1/EDJsOpgkH4KLyDS+Xjw3ytl3tmprE
zQBVKqZNNB0AHv+GfHpUoM44Q4IP8u0iJW/coq3ISaneLjAkGeNUg+FYmaaznxr6
+fgCHqGQxu0vgYQ4P5/mtluYfwKBgQDjE51KhP6ph+IiPv9wUQLHIryffjQ6QxNn
o84aAqb9DeCN3iodpe+9ikJXMLVUqInpeWLJomVZ+pUtq4L4fMF1D/Z7+4o3uRdw
t2KKAvKujgLhhsGlpCYUwDZYo3gwud0tMq140kd9PYNjGNEgBuX0TthZUoilHtRW
adWGOZ/BRQKBgQDrI+1ZdqrQBcRq91nJkEeFWY+wjfLhLH+vQOdMEDWg11O5vUfQ
NKDDl7VQAbgpPqPDjE7SYN6E9fVk3/XqbWKL3+S+Hr5/9nCxMZtqD+L+Xt3Jj8XQ
PD596TZWhCeorA3dYI+8eqB11fo39U226SbMzU8Zqbk/MCZHudQ0nx96+wKBgEK1
f27l9T5uqfMvmLExS2SfAtTEKam4DNpUl/ayMsaCriZfTvYYyn5fQLAGoi61uJY7
T9c2exnc8LhS+43ucJLoVpwDwI4wNP+rECrFRPAcziHdCcSUnY9ZDF4r3+JIp/5g
NfAZrmDPkmqpXr5O6H1GMG7FPVls3ipouw7MnO8VAoGBAIpzOUaTQvrCMO8QOwff
eYUqFdM7C1HjhuYKK0qOjRqRyumA+aqRpws7TLKxyt+AfgCh8n/HSVLakB7CscPy
TadBfmANPaHYHVXApC0vrcG4WeyoQO9bgXdu5h3EylbhR153BiaThaFjnbHtlej9
yVVeGwHfk5gaZvQlWzeapMWX
-----END PRIVATE KEY-----
```

### Step 3: デプロイ

#### VS Code拡張機能を使用（推奨）:
1. VS Codeで「Azure Functions」拡張機能をインストール
2. プロジェクトフォルダを開く
3. Azure拡張機能からデプロイ

#### ZIPデプロイ:
1. プロジェクトをZIPファイルに圧縮
2. Azure ポータルの「デプロイセンター」からZIPデプロイ実行

## 方法2: Azure CLI使用

### Step 1: Azureにログイン
```bash
az login
```

### Step 2: リソースグループ作成
```bash
az group create --name lineworks-bot-rg --location japaneast
```

### Step 3: Storage Account作成
```bash
az storage account create --name lineworksbotstore --resource-group lineworks-bot-rg --location japaneast --sku Standard_LRS
```

### Step 4: Function App作成
```bash
az functionapp create --resource-group lineworks-bot-rg --consumption-plan-location japaneast --runtime python --runtime-version 3.11 --functions-version 4 --name lineworks-bot-functions --storage-account lineworksbotstore --os-type linux
```

### Step 5: デプロイ
```bash
func azure functionapp publish lineworks-bot-functions
```

## エンドポイント確認

デプロイ後、以下のエンドポイントが利用可能：

- **ヘルスチェック**: `https://your-function-app.azurewebsites.net/api/health`
- **テスト**: `https://your-function-app.azurewebsites.net/api/test`
- **メッセージ送信**: `https://your-function-app.azurewebsites.net/api/send_message`

## テスト例

```bash
# ヘルスチェック
curl "https://your-function-app.azurewebsites.net/api/health"

# 環境変数確認
curl "https://your-function-app.azurewebsites.net/api/test"

# メッセージ送信
curl -X POST "https://your-function-app.azurewebsites.net/api/send_message" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "target_user_id", "message": "Hello from Azure Functions!"}'
```