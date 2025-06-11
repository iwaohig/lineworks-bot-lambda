import azure.functions as func
import logging
import json
import requests
import jwt
import time
import os
from datetime import datetime, timedelta

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# 受信したユーザーIDを記録するためのグローバル変数（実運用では永続化ストレージを使用）
received_user_ids = set()

# Webhookログを保存するためのグローバル変数（実運用では永続化ストレージを使用）
webhook_logs = []

def generate_jwt_token():
    """LINE WORKS API用のJWTトークンを生成（Service Account認証）"""
    try:
        client_id = os.environ.get('LINEWORKS_CLIENT_ID')
        service_account_id = os.environ.get('LINEWORKS_SERVICE_ACCOUNT_ID')
        private_key = os.environ.get('LINEWORKS_PRIVATE_KEY')
        
        if not all([client_id, service_account_id, private_key]):
            raise ValueError("Missing required environment variables: LINEWORKS_CLIENT_ID, LINEWORKS_SERVICE_ACCOUNT_ID, LINEWORKS_PRIVATE_KEY")
        
        # 現在時刻（Unix時間）
        current_time = int(time.time())
        
        # JWTペイロード（LINE WORKS Service Account認証公式仕様）
        payload = {
            'iss': client_id,               # アプリのClient ID
            'sub': service_account_id,      # Service Account ID
            'iat': current_time,            # JWT生成日時（Unix時間）
            'exp': current_time + 3600      # JWT満了日時（Unix時間、60分以内）
        }
        
        # 秘密鍵の形式確認とJWTトークン生成（RS256アルゴリズム）
        if private_key.startswith('-----BEGIN'):
            # PEM形式の秘密鍵
            token = jwt.encode(payload, private_key, algorithm='RS256')
        else:
            # Base64エンコードされた秘密鍵の場合
            import base64
            private_key_pem = base64.b64decode(private_key).decode('utf-8')
            token = jwt.encode(payload, private_key_pem, algorithm='RS256')
        
        logging.info(f"JWT generated successfully. iss: {client_id}, sub: {service_account_id}")
        return token
        
    except Exception as e:
        logging.error(f"JWT token generation failed: {str(e)}")
        return None

def get_access_token():
    """アクセストークンを取得（Service Account認証）"""
    try:
        jwt_token = generate_jwt_token()
        if not jwt_token:
            return None
            
        client_id = os.environ.get('LINEWORKS_CLIENT_ID')
        client_secret = os.environ.get('LINEWORKS_CLIENT_SECRET')
        
        if not all([client_id, client_secret]):
            raise ValueError("Missing required environment variables: LINEWORKS_CLIENT_ID, LINEWORKS_CLIENT_SECRET")
            
        # LINE WORKS API 2.0 トークンエンドポイント（公式仕様）
        url = "https://auth.worksmobile.com/oauth2/v2.0/token"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Service Account認証用のパラメータ（公式仕様）
        data = {
            'assertion': jwt_token,
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            'client_id': client_id,
            'client_secret': client_secret,
            'scope': 'bot'  # Bot APIスコープ
        }
        
        logging.info(f"Requesting access token from: {url}")
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code in [200, 201]:
            token_data = response.json()
            access_token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 3600)
            refresh_token = token_data.get('refresh_token')
            logging.info(f"Access token acquired successfully. Expires in: {expires_in} seconds")
            return access_token
        else:
            logging.error(f"Access token request failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logging.error(f"Access token acquisition failed: {str(e)}")
        return None

@app.route(route="send_message", methods=["POST"])
def send_message(req: func.HttpRequest) -> func.HttpResponse:
    """LINE WORKS Botでメッセージを送信"""
    logging.info('LINE WORKS Bot message send function processed a request.')
    
    try:
        # リクエストボディから必要な情報を取得
        req_body = req.get_json()
        if not req_body:
            return func.HttpResponse(
                json.dumps({"error": "Request body is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Bot IDは環境変数から取得（デフォルト値として設定済み）
        bot_id = req_body.get('bot_id') or os.environ.get('LINEWORKS_BOT_ID', '10207111')
        user_id = req_body.get('user_id')
        message_text = req_body.get('message', 'Hello from Azure Functions!')
        
        if not user_id:
            return func.HttpResponse(
                json.dumps({"error": "user_id is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # アクセストークン取得
        access_token = get_access_token()
        if not access_token:
            return func.HttpResponse(
                json.dumps({"error": "Failed to get access token"}),
                status_code=500,
                mimetype="application/json"
            )
        
        # メッセージ送信API呼び出し
        domain_id = os.environ.get('LINEWORKS_DOMAIN_ID')
        url = f"https://www.worksapis.com/v1.0/bots/{bot_id}/users/{user_id}/messages"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        message_data = {
            "content": {
                "type": "text",
                "text": message_text
            }
        }
        
        response = requests.post(url, headers=headers, json=message_data)
        
        if response.status_code == 200:
            return func.HttpResponse(
                json.dumps({
                    "success": True,
                    "message": "Message sent successfully",
                    "timestamp": datetime.now().isoformat()
                }),
                status_code=200,
                mimetype="application/json"
            )
        else:
            logging.error(f"Message send failed: {response.status_code} - {response.text}")
            return func.HttpResponse(
                json.dumps({
                    "error": "Failed to send message",
                    "status_code": response.status_code,
                    "response": response.text
                }),
                status_code=500,
                mimetype="application/json"
            )
            
    except Exception as e:
        logging.error(f"Function execution failed: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Internal server error: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="health", methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """ヘルスチェック用エンドポイント"""
    logging.info('Health check function processed a request.')
    
    return func.HttpResponse(
        json.dumps({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }),
        status_code=200,
        mimetype="application/json"
    )

@app.route(route="webhook", methods=["POST"])
def webhook_receiver(req: func.HttpRequest) -> func.HttpResponse:
    """LINE WORKSからのWebhookを受信"""
    logging.info('LINE WORKS Webhook function processed a request.')
    
    try:
        # リクエストボディを取得
        req_body = req.get_json()
        
        # 詳細なWebhookログを作成
        webhook_log_entry = {
            "timestamp": datetime.now().isoformat(),
            "request_body": req_body,
            "headers": {key: value for key, value in req.headers.items()},
            "content_type": req.headers.get('content-type'),
            "user_agent": req.headers.get('user-agent'),
            "raw_body_exists": req_body is not None,
            "body_keys": list(req_body.keys()) if req_body else [],
            "processing_status": "started"
        }
        
        # ログをリストに追加（最新10件を保持）
        webhook_logs.append(webhook_log_entry)
        if len(webhook_logs) > 10:
            webhook_logs.pop(0)
        
        if not req_body:
            webhook_log_entry["processing_status"] = "empty_body"
            logging.warning("Empty request body received")
            return func.HttpResponse("OK", status_code=200)
        
        # 受信データをログ出力（デバッグ用）
        logging.info(f"Webhook received: {json.dumps(req_body, indent=2, ensure_ascii=False)}")
        
        # リクエストヘッダーもログ出力
        headers_dict = {key: value for key, value in req.headers.items()}
        logging.info(f"Request headers: {json.dumps(headers_dict, indent=2, ensure_ascii=False)}")
        
        # イベントタイプを確認
        event_type = req_body.get('type')
        logging.info(f"Event type: {event_type}")
        
        # すべてのキーを確認（デバッグ用）
        logging.info(f"All keys in request: {list(req_body.keys())}")
        
        # ログエントリにイベント情報を追加
        webhook_log_entry["event_type"] = event_type
        webhook_log_entry["processing_status"] = "analyzing"
        
        # メッセージイベントの場合
        if event_type == 'message':
            # メッセージ情報を抽出
            source = req_body.get('source', {})
            content = req_body.get('content', {})  # LINE WORKSでは'content'キーを使用
            
            user_id = source.get('userId')
            message_type = content.get('type')
            message_text = content.get('text', '')
            
            # 受信したユーザーIDを記録
            if user_id:
                received_user_ids.add(user_id)
                logging.info(f"Added user ID to collection: {user_id}")
            
            logging.info(f"Message from user {user_id}: {message_text}")
            logging.info(f"Total unique users received: {len(received_user_ids)}")
            
            # ログエントリにメッセージ情報を追加
            webhook_log_entry["message_info"] = {
                "user_id": user_id,
                "message_type": message_type,
                "message_text": message_text,
                "source": source,
                "content": content
            }
            webhook_log_entry["processing_status"] = "message_parsed"
            
            # テキストメッセージの場合、エコー返信
            if message_type == 'text' and user_id and message_text:
                logging.info(f"Processing text message from user {user_id}: '{message_text}'")
                
                # 既存のsend_message機能を使ってエコー返信
                echo_message = f"受信しました: {message_text}"
                
                # アクセストークン取得
                logging.info("Getting access token...")
                access_token = get_access_token()
                if access_token:
                    logging.info("Access token acquired successfully")
                    
                    # メッセージ送信
                    bot_id = os.environ.get('LINEWORKS_BOT_ID', '10207111')
                    url = f"https://www.worksapis.com/v1.0/bots/{bot_id}/users/{user_id}/messages"
                    
                    headers = {
                        'Authorization': f'Bearer {access_token}',
                        'Content-Type': 'application/json'
                    }
                    
                    message_data = {
                        "content": {
                            "type": "text",
                            "text": echo_message
                        }
                    }
                    
                    logging.info(f"Sending echo message to {url}")
                    logging.info(f"Message data: {json.dumps(message_data, ensure_ascii=False)}")
                    
                    response = requests.post(url, headers=headers, json=message_data)
                    
                    logging.info(f"Response status: {response.status_code}")
                    logging.info(f"Response headers: {dict(response.headers)}")
                    logging.info(f"Response body: {response.text}")
                    
                    if response.status_code in [200, 201]:
                        logging.info(f"Echo message sent successfully to user {user_id}")
                        webhook_log_entry["echo_response"] = {
                            "status": "success",
                            "status_code": response.status_code,
                            "echo_message": echo_message
                        }
                    else:
                        logging.error(f"Failed to send echo message: {response.status_code} - {response.text}")
                        
                        # エラーの詳細情報をログ出力
                        try:
                            error_detail = response.json()
                            logging.error(f"Error detail: {json.dumps(error_detail, ensure_ascii=False)}")
                            webhook_log_entry["echo_response"] = {
                                "status": "failed",
                                "status_code": response.status_code,
                                "error_detail": error_detail,
                                "response_text": response.text
                            }
                        except:
                            logging.error("Failed to parse error response as JSON")
                            webhook_log_entry["echo_response"] = {
                                "status": "failed",
                                "status_code": response.status_code,
                                "response_text": response.text,
                                "parse_error": "Failed to parse JSON"
                            }
                else:
                    logging.error("Failed to get access token for echo reply")
                    webhook_log_entry["echo_response"] = {
                        "status": "failed",
                        "error": "Failed to get access token"
                    }
            else:
                logging.warning(f"Message conditions not met - type: {message_type}, user_id: {user_id}, text: '{message_text}'")
                webhook_log_entry["echo_response"] = {
                    "status": "skipped",
                    "reason": "Message conditions not met",
                    "conditions": {
                        "message_type": message_type,
                        "user_id_exists": bool(user_id),
                        "message_text_exists": bool(message_text)
                    }
                }
        
        # 処理完了をログに記録
        webhook_log_entry["processing_status"] = "completed"
        webhook_log_entry["completion_time"] = datetime.now().isoformat()
        
        # Webhook応答（必ず200を返す）
        return func.HttpResponse("OK", status_code=200)
        
    except Exception as e:
        logging.error(f"Webhook processing failed: {str(e)}")
        
        # エラー情報をログに記録
        if 'webhook_log_entry' in locals():
            webhook_log_entry["processing_status"] = "error"
            webhook_log_entry["error"] = str(e)
            webhook_log_entry["completion_time"] = datetime.now().isoformat()
        
        # エラーが発生してもLINE WORKSには200を返す
        return func.HttpResponse("OK", status_code=200)

@app.route(route="webhook_logs", methods=["GET"])
def get_webhook_logs(req: func.HttpRequest) -> func.HttpResponse:
    """Webhookの詳細ログを取得"""
    logging.info('Get webhook logs function processed a request.')
    
    try:
        # クエリパラメータで件数制限
        limit = req.params.get('limit')
        if limit:
            try:
                limit = int(limit)
                logs_to_return = webhook_logs[-limit:] if limit > 0 else webhook_logs
            except ValueError:
                logs_to_return = webhook_logs
        else:
            logs_to_return = webhook_logs
        
        return func.HttpResponse(
            json.dumps({
                "success": True,
                "webhook_logs": logs_to_return,
                "total_count": len(webhook_logs),
                "returned_count": len(logs_to_return),
                "timestamp": datetime.now().isoformat()
            }, ensure_ascii=False, indent=2),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Get webhook logs function failed: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Internal server error: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="received_users", methods=["GET"])
def get_received_users(req: func.HttpRequest) -> func.HttpResponse:
    """Webhookで受信したユーザーID一覧を取得"""
    logging.info('Get received users function processed a request.')
    
    try:
        return func.HttpResponse(
            json.dumps({
                "success": True,
                "received_user_ids": list(received_user_ids),
                "total_count": len(received_user_ids),
                "timestamp": datetime.now().isoformat()
            }, ensure_ascii=False),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Get received users function failed: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Internal server error: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="get_users", methods=["GET"])
def get_users(req: func.HttpRequest) -> func.HttpResponse:
    """ドメイン内のユーザー一覧を取得"""
    logging.info('Get users function processed a request.')
    
    try:
        # アクセストークン取得
        access_token = get_access_token()
        if not access_token:
            return func.HttpResponse(
                json.dumps({"error": "Failed to get access token"}),
                status_code=500,
                mimetype="application/json"
            )
        
        # ユーザー一覧取得API呼び出し
        domain_id = os.environ.get('LINEWORKS_DOMAIN_ID')
        url = f"https://www.worksapis.com/v1.0/users"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # パラメータでページサイズを指定
        params = {
            'limit': 10  # 最初の10ユーザーを取得
        }
        
        logging.info(f"Requesting users from: {url}")
        response = requests.get(url, headers=headers, params=params)
        
        logging.info(f"Response status: {response.status_code}")
        logging.info(f"Response body: {response.text}")
        
        if response.status_code in [200, 201]:
            users_data = response.json()
            return func.HttpResponse(
                json.dumps({
                    "success": True,
                    "users": users_data,
                    "timestamp": datetime.now().isoformat()
                }, ensure_ascii=False),
                status_code=200,
                mimetype="application/json"
            )
        else:
            return func.HttpResponse(
                json.dumps({
                    "error": "Failed to get users",
                    "status_code": response.status_code,
                    "response": response.text
                }),
                status_code=500,
                mimetype="application/json"
            )
            
    except Exception as e:
        logging.error(f"Get users function failed: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Internal server error: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="test", methods=["GET"])
def test_function(req: func.HttpRequest) -> func.HttpResponse:
    """テスト用の簡単な関数"""
    logging.info('Test function processed a request.')
    
    name = req.params.get('name', 'World')
    
    return func.HttpResponse(
        json.dumps({
            "message": f"Hello, {name}!",
            "timestamp": datetime.now().isoformat(),
            "env_check": {
                "has_client_id": bool(os.environ.get('LINEWORKS_CLIENT_ID')),
                "has_client_secret": bool(os.environ.get('LINEWORKS_CLIENT_SECRET')),
                "has_service_account_id": bool(os.environ.get('LINEWORKS_SERVICE_ACCOUNT_ID')),
                "has_private_key": bool(os.environ.get('LINEWORKS_PRIVATE_KEY')),
                "has_domain_id": bool(os.environ.get('LINEWORKS_DOMAIN_ID')),
                "has_bot_id": bool(os.environ.get('LINEWORKS_BOT_ID'))
            }
        }),
        status_code=200,
        mimetype="application/json"
    )