#!/usr/bin/env python3
"""
debug_gumroad.py - 調試 Gumroad 產品 ID 映射問題
"""
import requests
import os
import json

def debug_gumroad_products():
    """調試 Gumroad 產品設置"""
    
    access_token = os.environ.get('GUMROAD_ACCESS_TOKEN')
    if not access_token:
        print("❌ 請設置 GUMROAD_ACCESS_TOKEN 環境變數")
        return
    
    print("🚀 開始調試 Gumroad 產品設置...")
    print("=" * 60)
    
    # 1. 獲取所有產品
    try:
        url = "https://api.gumroad.com/v2/products"
        params = {'access_token': access_token}
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get('success'):
            products = result.get('products', [])
            print(f"📦 找到 {len(products)} 個產品")
            print()
            
            # 2. 顯示產品詳情
            for i, product in enumerate(products, 1):
                print(f"🔹 產品 {i}:")
                print(f"   名稱: {product.get('name', 'N/A')}")
                print(f"   ID: {product.get('id', 'N/A')}")
                print(f"   價格: {product.get('formatted_price', 'N/A')}")
                print(f"   自定義連結: {product.get('custom_permalink', 'N/A')}")
                print(f"   短網址: {product.get('short_url', 'N/A')}")
                print(f"   已發布: {'✅' if product.get('published') else '❌'}")
                print(f"   銷售數量: {product.get('sales_count', 0)}")
                print()
            
            # 3. 檢查環境變數映射
            print("🔧 環境變數產品 ID 檢查:")
            print("-" * 40)
            
            env_products = {
                'GUMROAD_TRIAL_PRODUCT_ID': os.environ.get('GUMROAD_TRIAL_PRODUCT_ID'),
                'GUMROAD_MONTHLY_PRODUCT_ID': os.environ.get('GUMROAD_MONTHLY_PRODUCT_ID'),
                'GUMROAD_QUARTERLY_PRODUCT_ID': os.environ.get('GUMROAD_QUARTERLY_PRODUCT_ID')
            }
            
            for env_name, env_id in env_products.items():
                print(f"{env_name}: {env_id}")
                
                if env_id:
                    # 查找匹配的產品
                    matched_product = None
                    for product in products:
                        if (product.get('id') == env_id or 
                            product.get('custom_permalink') == env_id):
                            matched_product = product
                            break
                    
                    if matched_product:
                        print(f"  ✅ 找到匹配產品: {matched_product.get('name')}")
                    else:
                        print(f"  ❌ 找不到匹配的產品！")
                        print(f"  💡 建議檢查產品 ID 是否正確")
                else:
                    print(f"  ⚠️ 環境變數未設置")
                print()
            
            # 4. 生成建議的環境變數配置
            print("💡 建議的環境變數配置:")
            print("-" * 40)
            
            if len(products) >= 3:
                # 根據價格排序，推測方案
                sorted_products = sorted(products, key=lambda x: x.get('price', 0))
                
                print("# 根據產品價格推測的配置:")
                if len(sorted_products) > 0:
                    print(f"GUMROAD_TRIAL_PRODUCT_ID={sorted_products[0]['id']}")
                    print(f"# {sorted_products[0]['name']} - {sorted_products[0]['formatted_price']}")
                
                if len(sorted_products) > 1:
                    print(f"GUMROAD_MONTHLY_PRODUCT_ID={sorted_products[1]['id']}")
                    print(f"# {sorted_products[1]['name']} - {sorted_products[1]['formatted_price']}")
                
                if len(sorted_products) > 2:
                    print(f"GUMROAD_QUARTERLY_PRODUCT_ID={sorted_products[2]['id']}")
                    print(f"# {sorted_products[2]['name']} - {sorted_products[2]['formatted_price']}")
            
            print()
            print("📋 所有產品 ID 列表:")
            for product in products:
                print(f"# {product['name']}: {product['id']}")
            
        else:
            print(f"❌ API 調用失敗: {result}")
            
    except requests.RequestException as e:
        print(f"❌ 網路請求失敗: {str(e)}")
    except Exception as e:
        print(f"❌ 未知錯誤: {str(e)}")
    
    print()
    print("🔍 Webhook 調試信息:")
    print("-" * 40)
    webhook_url = os.environ.get('WEBHOOK_BASE_URL', 'https://scrilab.onrender.com')
    if not webhook_url.startswith('http'):
        webhook_url = f"https://{webhook_url}"
    webhook_url = webhook_url.rstrip('/') + '/gumroad/webhook'
    
    print(f"Webhook URL: {webhook_url}")
    print()
    print("請在 Gumroad 設置中的 'Advanced' -> 'Ping endpoint' 設置此 URL")
    

def test_webhook_payload():
    """測試 webhook 數據格式"""
    print("🧪 測試 Webhook 數據格式:")
    print("-" * 40)
    
    # 模擬的 webhook 數據
    test_webhook = {
        'seller_id': 'test_seller_id',
        'product_id': 'G9eGOb-BdZDHg8EWVVMuqg==',  # 從錯誤日誌中看到的
        'product_name': 'Scrilab Artale Trial Service',
        'permalink': 'yollr',
        'email': 'test@example.com',
        'price': '500',  # 5.00 USD in cents
        'currency': 'usd',
        'quantity': '1',
        'order_number': '12345678',
        'sale_id': 'test_sale_id',
        'sale_timestamp': '2025-01-15T12:00:00Z',
        'full_name': 'Test User',
        'ip_country': 'Taiwan',
        'refunded': 'false',
        'resource_name': 'sale'
    }
    
    print("模擬的 Webhook 數據:")
    print(json.dumps(test_webhook, indent=2, ensure_ascii=False))
    print()
    
    print("❗ 關鍵問題：")
    print(f"Webhook 中的 product_id: {test_webhook['product_id']}")
    print("這個 ID 需要與您的環境變數中的產品 ID 匹配！")


if __name__ == "__main__":
    debug_gumroad_products()
    print()
    test_webhook_payload()