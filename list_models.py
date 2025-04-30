#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
利用可能なモデル一覧を取得するクライアント
"""

import requests
import json

# LiteLLM Proxy APIのベースURL
BASE_URL = "http://0.0.0.0:4000/v1"

def list_available_models():
    """
    利用可能なモデル一覧を取得
    
    Returns:
        モデルリスト
    """
    # エンドポイント
    endpoint = f"{BASE_URL}/models"
    
    # ヘッダー
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        # API呼び出し
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()  # エラーがあれば例外を発生
        
        # レスポンスをパース
        result = response.json()
        
        print("利用可能なモデル一覧:")
        for model in result.get("data", []):
            print(f"- {model.get('id')}")
        
        return result
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        # デバッグ情報
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"レスポンス: {e.response.text}")
        return None

if __name__ == "__main__":
    list_available_models()
