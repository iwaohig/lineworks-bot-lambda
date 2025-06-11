import json
import logging
import requests
import jwt
import time
import os
from datetime import datetime, timedelta

# Lambda用のロガー設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 受信したユーザーIDを記録するためのグローバル変数（実運用では DynamoDB を使用）
received_user_ids = set()

# Webhookログを保存するためのグローバル変数（実運用では DynamoDB を使用）
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
        logger.info(f"Private key length: {len(private_key)}")
        
        if private_key.startswith('-----BEGIN'):
            # PEM形式の秘密鍵（パイプ区切りの改行を置換）
            private_key_pem = private_key.replace('|', '\n')
            logger.info(f"Using PEM format private key")
        else:
            # Base64エンコードされた秘密鍵の場合
            import base64
            try:
                private_key_pem = base64.b64decode(private_key).decode('utf-8')
                logger.info(f"Decoded private key starts with: {private_key_pem[:50]}...")
                logger.info(f"Decoded private key ends with: ...{private_key_pem[-50:]}")
            except Exception as decode_error:
                logger.error(f"Failed to decode base64 private key: {str(decode_error)}")
                raise ValueError(f"Invalid private key format: {str(decode_error)}")
        
        # 秘密鍵の正規化（改行の修正）
        if '-----BEGIN PRIVATE KEY-----' in private_key_pem and not private_key_pem.startswith('-----BEGIN'):
            # 改行の問題を修正
            lines = private_key_pem.replace('\r\n', '\n').replace('\r', '\n').split('\n')
            private_key_pem = '\n'.join(line.strip() for line in lines if line.strip())
            logger.info(f"Normalized private key format")
        
        # JWTトークン生成（cryptographyライブラリによる検証はPyJWTが内部で行う）
        try:
            logger.info("Attempting JWT token generation...")
            
            # cryptographyライブラリを使用して秘密鍵をロード
            from cryptography.hazmat.primitives import serialization
            try:
                # PKCS#8形式として読み込み
                private_key_obj = serialization.load_pem_private_key(
                    private_key_pem.encode('utf-8'), 
                    password=None
                )
                logger.info("Private key loaded successfully as PKCS#8")
            except Exception as pkcs8_error:
                logger.error(f"PKCS#8 load failed: {str(pkcs8_error)}")
                
                # PKCS#1形式として試行
                try:
                    # RSA PRIVATE KEY形式に変換して試行
                    rsa_key_content = private_key_pem.replace('-----BEGIN PRIVATE KEY-----', '-----BEGIN RSA PRIVATE KEY-----')
                    rsa_key_content = rsa_key_content.replace('-----END PRIVATE KEY-----', '-----END RSA PRIVATE KEY-----')
                    private_key_obj = serialization.load_pem_private_key(
                        rsa_key_content.encode('utf-8'), 
                        password=None
                    )
                    logger.info("Private key loaded successfully as PKCS#1 (RSA)")
                except Exception as pkcs1_error:
                    logger.error(f"PKCS#1 load failed: {str(pkcs1_error)}")
                    raise ValueError(f"Could not load private key: {str(pkcs8_error)}")
            
            # PyJWTでトークン生成
            token = jwt.encode(payload, private_key_obj, algorithm='RS256')
            logger.info("JWT token generated successfully")
        except Exception as jwt_error:
            logger.error(f"JWT encoding failed: {str(jwt_error)}")
            raise ValueError(f"JWT generation failed: {str(jwt_error)}")
        
        logger.info(f"JWT generated successfully. iss: {client_id}, sub: {service_account_id}")
        return token
        
    except Exception as e:
        logger.error(f"JWT token generation failed: {str(e)}")
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
        
        logger.info(f"Requesting access token from: {url}")
        logger.info(f"Request headers: {headers}")
        logger.info(f"Request data keys: {list(data.keys())}")
        logger.info(f"JWT token length: {len(jwt_token)}")
        
        response = requests.post(url, headers=headers, data=data)
        
        logger.info(f"Token response status: {response.status_code}")
        logger.info(f"Token response headers: {dict(response.headers)}")
        logger.info(f"Token response body: {response.text}")
        
        if response.status_code in [200, 201]:
            token_data = response.json()
            access_token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 3600)
            refresh_token = token_data.get('refresh_token')
            logger.info(f"Access token acquired successfully. Expires in: {expires_in} seconds")
            return access_token
        else:
            logger.error(f"Access token request failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Access token acquisition failed: {str(e)}")
        return None

def send_message_handler(event, context):
    """LINE WORKS Botでメッセージを送信"""
    logger.info('LINE WORKS Bot message send function processed a request.')
    
    try:
        # API Gateway からのリクエストボディを取得
        logger.info(f"Event body type: {type(event.get('body'))}")
        logger.info(f"Event body content: {event.get('body')}")
        
        if isinstance(event.get('body'), str):
            try:
                # API Gateway からのJSONでエスケープ問題が発生する場合の対処
                body_str = event['body']
                logger.info(f"Raw body string: {repr(body_str)}")
                
                # 二重エスケープされたJSONを修正
                if '\\' in body_str:
                    # バックスラッシュのエスケープ問題を修正
                    body_str = body_str.replace('\\!', '!')
                    body_str = body_str.replace('\\?', '?')
                    body_str = body_str.replace('\\&', '&')
                    logger.info(f"Fixed body string: {repr(body_str)}")
                
                req_body = json.loads(body_str)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {str(e)}")
                logger.error(f"Original body: {repr(event.get('body'))}")
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({"error": f"JSON decode error: {str(e)}"})
                }
        else:
            req_body = event.get('body', {})
            
        if not req_body:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "Request body is required"})
            }
        
        # Bot IDは環境変数から取得（デフォルト値として設定済み）
        bot_id = req_body.get('bot_id') or os.environ.get('LINEWORKS_BOT_ID', '10207111')
        user_id = req_body.get('user_id')
        message_text = req_body.get('message', 'Hello from AWS Lambda!')
        
        if not user_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "user_id is required"})
            }
        
        # アクセストークン取得
        access_token = get_access_token()
        if not access_token:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "Failed to get access token"})
            }
        
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
        
        if response.status_code in [200, 201]:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    "success": True,
                    "message": "Message sent successfully",
                    "timestamp": datetime.now().isoformat()
                })
            }
        else:
            logger.error(f"Message send failed: {response.status_code} - {response.text}")
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    "error": "Failed to send message",
                    "status_code": response.status_code,
                    "response": response.text
                })
            }
            
    except Exception as e:
        logger.error(f"Function execution failed: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": f"Internal server error: {str(e)}"})
        }

def health_check_handler(event, context):
    """ヘルスチェック用エンドポイント"""
    logger.info('Health check function processed a request.')
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        })
    }

def webhook_handler(event, context):
    """LINE WORKSからのWebhookを受信"""
    logger.info('LINE WORKS Webhook function processed a request.')
    
    try:
        # API Gateway からのリクエストボディを取得
        logger.info(f"Event body type: {type(event.get('body'))}")
        logger.info(f"Event body content: {event.get('body')}")
        
        if isinstance(event.get('body'), str):
            try:
                # API Gateway からのJSONでエスケープ問題が発生する場合の対処
                body_str = event['body']
                logger.info(f"Raw body string: {repr(body_str)}")
                
                # 二重エスケープされたJSONを修正
                if '\\' in body_str:
                    # バックスラッシュのエスケープ問題を修正
                    body_str = body_str.replace('\\!', '!')
                    body_str = body_str.replace('\\?', '?')
                    body_str = body_str.replace('\\&', '&')
                    logger.info(f"Fixed body string: {repr(body_str)}")
                
                req_body = json.loads(body_str)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error in webhook: {str(e)}")
                logger.error(f"Original body: {repr(event.get('body'))}")
                # Webhookの場合はエラーでも200を返す（LINE WORKSの仕様）
                return {
                    'statusCode': 200,
                    'body': 'OK'
                }
        else:
            req_body = event.get('body', {})
        
        # 詳細なWebhookログを作成
        webhook_log_entry = {
            "timestamp": datetime.now().isoformat(),
            "request_body": req_body,
            "headers": event.get('headers', {}),
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
            logger.warning("Empty request body received")
            return {
                'statusCode': 200,
                'body': 'OK'
            }
        
        # 受信データをログ出力（デバッグ用）
        logger.info(f"Webhook received: {json.dumps(req_body, indent=2, ensure_ascii=False)}")
        
        # リクエストヘッダーもログ出力
        headers_dict = event.get('headers', {})
        logger.info(f"Request headers: {json.dumps(headers_dict, indent=2, ensure_ascii=False)}")
        
        # イベントタイプを確認
        event_type = req_body.get('type')
        logger.info(f"Event type: {event_type}")
        
        # すべてのキーを確認（デバッグ用）
        logger.info(f"All keys in request: {list(req_body.keys())}")
        
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
                logger.info(f"Added user ID to collection: {user_id}")
            
            logger.info(f"Message from user {user_id}: {message_text}")
            logger.info(f"Total unique users received: {len(received_user_ids)}")
            
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
                logger.info(f"Processing text message from user {user_id}: '{message_text}'")
                
                # 既存のsend_message機能を使ってエコー返信
                echo_message = f"受信しました: {message_text}"
                
                # アクセストークン取得
                logger.info("Getting access token...")
                access_token = get_access_token()
                if access_token:
                    logger.info("Access token acquired successfully")
                    
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
                    
                    logger.info(f"Sending echo message to {url}")
                    logger.info(f"Message data: {json.dumps(message_data, ensure_ascii=False)}")
                    
                    response = requests.post(url, headers=headers, json=message_data)
                    
                    logger.info(f"Response status: {response.status_code}")
                    logger.info(f"Response headers: {dict(response.headers)}")
                    logger.info(f"Response body: {response.text}")
                    
                    if response.status_code in [200, 201]:
                        logger.info(f"Echo message sent successfully to user {user_id}")
                        webhook_log_entry["echo_response"] = {
                            "status": "success",
                            "status_code": response.status_code,
                            "echo_message": echo_message
                        }
                    else:
                        logger.error(f"Failed to send echo message: {response.status_code} - {response.text}")
                        
                        # エラーの詳細情報をログ出力
                        try:
                            error_detail = response.json()
                            logger.error(f"Error detail: {json.dumps(error_detail, ensure_ascii=False)}")
                            webhook_log_entry["echo_response"] = {
                                "status": "failed",
                                "status_code": response.status_code,
                                "error_detail": error_detail,
                                "response_text": response.text
                            }
                        except:
                            logger.error("Failed to parse error response as JSON")
                            webhook_log_entry["echo_response"] = {
                                "status": "failed",
                                "status_code": response.status_code,
                                "response_text": response.text,
                                "parse_error": "Failed to parse JSON"
                            }
                else:
                    logger.error("Failed to get access token for echo reply")
                    webhook_log_entry["echo_response"] = {
                        "status": "failed",
                        "error": "Failed to get access token"
                    }
            else:
                logger.warning(f"Message conditions not met - type: {message_type}, user_id: {user_id}, text: '{message_text}'")
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
        return {
            'statusCode': 200,
            'body': 'OK'
        }
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {str(e)}")
        
        # エラー情報をログに記録
        if 'webhook_log_entry' in locals():
            webhook_log_entry["processing_status"] = "error"
            webhook_log_entry["error"] = str(e)
            webhook_log_entry["completion_time"] = datetime.now().isoformat()
        
        # エラーが発生してもLINE WORKSには200を返す
        return {
            'statusCode': 200,
            'body': 'OK'
        }

def test_handler(event, context):
    """テスト用の簡単な関数"""
    logger.info('Test function processed a request.')
    
    query_params = event.get('queryStringParameters') or {}
    name = query_params.get('name', 'World')
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
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
        })
    }

# Lambda ハンドラー関数（デフォルト）
def lambda_handler(event, context):
    """メインのLambdaハンドラー - API Gatewayルーティング用"""
    
    # API Gateway のパスとメソッドを取得
    path = event.get('path', '/')
    method = event.get('httpMethod', 'GET')
    
    logger.info(f"Request: {method} {path}")
    
    # ルーティング
    if path == '/send_message' and method == 'POST':
        return send_message_handler(event, context)
    elif path == '/health' and method == 'GET':
        return health_check_handler(event, context)
    elif path == '/webhook' and method == 'POST':
        return webhook_handler(event, context)
    elif path == '/test' and method == 'GET':
        return test_handler(event, context)
    else:
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": "Not Found"})
        }