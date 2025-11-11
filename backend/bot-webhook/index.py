import json
import os
from datetime import datetime
from typing import Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Business: Receives dialog data from Telegram bot and stores in database
    Args: event - dict with httpMethod, body (JSON with user_id, telegram_id, name, tokens, model, premium)
          context - object with request_id attribute
    Returns: HTTP response dict with success/error status
    '''
    method: str = event.get('httpMethod', 'POST')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-Api-Key',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    if method == 'POST':
        body_data = json.loads(event.get('body', '{}'))
        
        telegram_id = body_data.get('telegram_id')
        name = body_data.get('name', 'Пользователь')
        tokens = body_data.get('tokens', 0)
        model = body_data.get('model', 'GPT-3.5')
        premium = body_data.get('premium', False)
        email = body_data.get('email')
        
        if not telegram_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'telegram_id is required'}),
                'isBase64Encoded': False
            }
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute(
            "SELECT id, total_tokens, dialogs_count FROM users WHERE telegram_id = %s",
            (telegram_id,)
        )
        user = cur.fetchone()
        
        if user:
            user_id = user['id']
            new_total_tokens = user['total_tokens'] + tokens
            new_dialogs_count = user['dialogs_count'] + 1
            
            cur.execute(
                "UPDATE users SET total_tokens = %s, dialogs_count = %s, last_active = %s, premium = %s WHERE id = %s",
                (new_total_tokens, new_dialogs_count, datetime.now(), premium, user_id)
            )
        else:
            cur.execute(
                "INSERT INTO users (telegram_id, name, email, premium, total_tokens, dialogs_count, last_active) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
                (telegram_id, name, email, premium, tokens, 1, datetime.now())
            )
            user_id = cur.fetchone()['id']
        
        cur.execute(
            "INSERT INTO dialogs (user_id, telegram_id, tokens, model, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (user_id, telegram_id, tokens, model, 'Завершён', datetime.now(), datetime.now())
        )
        dialog_id = cur.fetchone()['id']
        
        today = datetime.now().date()
        cur.execute(
            "SELECT id, total_tokens, active_users FROM token_stats WHERE date = %s",
            (today,)
        )
        stats = cur.fetchone()
        
        if stats:
            cur.execute(
                "UPDATE token_stats SET total_tokens = total_tokens + %s WHERE date = %s",
                (tokens, today)
            )
        else:
            cur.execute(
                "SELECT COUNT(DISTINCT telegram_id) as count FROM dialogs WHERE DATE(created_at) = %s",
                (today,)
            )
            active_count = cur.fetchone()['count']
            
            cur.execute(
                "INSERT INTO token_stats (date, total_tokens, active_users) VALUES (%s, %s, %s)",
                (today, tokens, active_count)
            )
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': True,
                'dialog_id': dialog_id,
                'user_id': user_id
            }),
            'isBase64Encoded': False
        }
    
    if method == 'GET':
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'status': 'Bot webhook API is running'}),
            'isBase64Encoded': False
        }
    
    return {
        'statusCode': 405,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'error': 'Method not allowed'}),
        'isBase64Encoded': False
    }
