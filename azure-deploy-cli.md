# Azure Functions CLI デプロイ手順

## 前提条件

Azure ポータルで事前にFunction Appを作成する必要があります：

### Step 1: Azure ポータルでFunction App作成

1. [Azure ポータル](https://portal.azure.com) にログイン
2. 「リソースの作成」→「Function App」を選択
3. 基本設定：
   - **Function App名**: `lineworks-bot-functions`（ユニークな名前に変更可能）
   - **ランタイムスタック**: Python 3.11
   - **リージョン**: Japan East
   - **オペレーティングシステム**: Linux
   - **プラン**: 従量課金プラン

### Step 2: 環境変数設定

Function App作成後、「構成」→「アプリケーション設定」で環境変数を追加。

## CLI デプロイ手順

### 方法1: Azure CLIと組み合わせ（推奨）

```bash
# 1. Azure CLIでログイン（ブラウザが開きます）
az login

# 2. Functions Core Toolsでデプロイ
func azure functionapp publish lineworks-bot-functions

# 3. 環境変数設定（オプション）
func azure functionapp publish lineworks-bot-functions --publish-local-settings
```

### 方法2: アクセストークン使用

```bash
# 1. Azure CLIでアクセストークン取得
az account get-access-token --query accessToken --output tsv

# 2. トークンを使ってデプロイ
func azure functionapp publish lineworks-bot-functions --access-token YOUR_ACCESS_TOKEN
```

### 方法3: 現在の環境での手動デプロイ

Azure CLIが利用できない場合：

```bash
# 1. プロジェクトをZIPに圧縮
zip -r deployment.zip . -x "*.git*" "local.settings.json" "__pycache__/*" ".vscode/*" "*.md"

# 2. Azure ポータルの「デプロイセンター」→「ZIP デプロイ」でアップロード
```

## 環境変数設定コマンド

Azure CLIが利用可能な場合：

```bash
az functionapp config appsettings set --name lineworks-bot-functions --resource-group YOUR_RESOURCE_GROUP --settings \
  "LINEWORKS_CLIENT_ID=MhOIRuvy6pmxUcNTAxTg" \
  "LINEWORKS_CLIENT_SECRET=VjlkX_IIxs" \
  "LINEWORKS_SERVICE_ACCOUNT_ID=wpumx.serviceaccount@lwugdev" \
  "LINEWORKS_DOMAIN_ID=400083023" \
  "LINEWORKS_BOT_ID=10207111" \
  "LINEWORKS_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----
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
-----END PRIVATE KEY-----"
```

## デプロイ確認

```bash
# 関数一覧表示
func azure functionapp list-functions lineworks-bot-functions

# ログストリーム
func azure functionapp logstream lineworks-bot-functions
```

## トラブルシューティング

### 一般的なエラー

1. **認証エラー**: `az login`でAzureにログインしてください
2. **Function Appが見つからない**: Function App名を確認してください
3. **権限エラー**: Azure リソースへの適切な権限があることを確認してください

### デバッグ方法

```bash
# 詳細ログでデプロイ
func azure functionapp publish lineworks-bot-functions --verbose

# 設定のみ公開
func azure functionapp publish lineworks-bot-functions --publish-settings-only
```