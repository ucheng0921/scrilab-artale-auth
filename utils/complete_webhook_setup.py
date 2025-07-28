#!/usr/bin/env python3
"""
complete_webhook_setup.py - 完整的 Gumroad Webhook 設置指南
"""
import requests
import os
import hmac
import hashlib

def step1_check_environment():
    """步驟 1：檢查環境變數"""
    print("🔍 步驟 1：檢查環境變數")
    print("-" * 40)
    
    access_token = os.environ.get('GUMROAD_ACCESS_TOKEN')
    webhook_secret = os.environ.get('GUMROAD_WEBHOOK_SECRET')
    webhook_base_url = os.environ.get('WEBHOOK_BASE_URL')
    
    print(f"GUMROAD_ACCESS_TOKEN: {'✅ 已設置' if access_token else '❌ 未設置'}")
    print(f"GUMROAD_WEBHOOK_SECRET: {'✅ 已設置' if webhook_secret else '❌ 未設置'}")
    print(f"WEBHOOK_BASE_URL: {'✅ 已設置' if webhook_base_url else '❌ 未設置'}")
    
    if webhook_secret:
        print(f"Secret 預覽: {webhook_secret[:8]}...")
    
    print()
    return access_token, webhook_secret, webhook_base_url

def step2_remove_ping_endpoint(access_token):
    """步驟 2：移除舊的 Ping Endpoint"""
    print("🗑️ 步驟 2：移除舊的 Ping Endpoint")
    print("-" * 40)
    
    try:
        url = "https://api.gumroad.com/v2/user"
        data = {
            'access_token': access_token,
            'ping_url': ''  # 空字串移除 ping endpoint
        }
        
        response = requests.put(url, data=data, timeout=30)
        result = response.json()
        
        if result.get('success'):
            print("✅ 已移除舊的 Ping Endpoint")
        else:
            print(f"⚠️ 移除 Ping Endpoint 時發生問題: {result}")
    
    except Exception as e:
        print(f"❌ 移除 Ping Endpoint 失敗: {str(e)}")
    
    print()

def step3_setup_resource_subscriptions(access_token, webhook_url):
    """步驟 3：設置 Resource Subscriptions"""
    print("⚙️ 步驟 3：設置 Resource Subscriptions")
    print("-" * 40)
    
    resource_types = ['sale', 'refund', 'cancellation']
    success_count = 0
    
    for resource_name in resource_types:
        try:
            print(f"設置 {resource_name} webhook...")
            
            # 刪除現有訂閱
            existing_subs = get_existing_subscriptions(access_token, resource_name)
            for sub in existing_subs:
                delete_subscription(access_token, sub['id'])
            
            # 創建新訂閱
            create_url = "https://api.gumroad.com/v2/resource_subscriptions"
            create_data = {
                'access_token': access_token,
                'resource_name': resource_name,
                'post_url': webhook_url
            }
            
            response = requests.put(create_url, data=create_data, timeout=30)
            result = response.json()
            
            if result.get('success'):
                print(f"  ✅ {resource_name} webhook 設置成功")
                success_count += 1
            else:
                print(f"  ❌ {resource_name} webhook 設置失敗: {result}")
        
        except Exception as e:
            print(f"  ❌ 設置 {resource_name} webhook 錯誤: {str(e)}")
    
    print(f"\n🎯 Resource Subscriptions 設置完成: {success_count}/{len(resource_types)}")
    print()
    
    return success_count > 0

def get_existing_subscriptions(access_token, resource_name):
    """獲取現有訂閱"""
    try:
        url = "https://api.gumroad.com/v2/resource_subscriptions"
        params = {
            'access_token': access_token,
            'resource_name': resource_name
        }
        
        response = requests.get(url, params=params, timeout=10)
        result = response.json()
        
        if result.get('success'):
            return result.get('resource_subscriptions', [])
        return []
    
    except Exception:
        return []

def delete_subscription(access_token, subscription_id):
    """刪除訂閱"""
    try:
        url = f"https://api.gumroad.com/v2/resource_subscriptions/{subscription_id}"
        data = {'access_token': access_token}
        
        requests.delete(url, data=data, timeout=10)
    except Exception:
        pass

def step4_test_webhook(webhook_url, webhook_secret):
    """步驟 4：測試 Webhook"""
    print("🧪 步驟 4：測試 Webhook 簽名")
    print("-" * 40)
    
    # 模擬 webhook 數據
    test_data = {
        'sale_id': 'test_sale_123',
        'product_id': 'G9eGOb-BdZDHg8EWVVMuqg==',
        'email': 'test@example.com',
        'price': '167'
    }
    
    # 將數據轉為字串（模擬 Gumroad 的格式）
    test_payload = '&'.join([f"{k}={v}" for k, v in test_data.items()])
    
    # 生成簽名
    if webhook_secret:
        signature = hmac.new(
            webhook_secret.encode(),
            test_payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        print(f"測試數據: {test_payload}")
        print(f"生成簽名: {signature}")
        print("✅ 簽名生成成功")
    else:
        print("❌ 無法測試簽名，未設置 WEBHOOK_SECRET")
    
    print()

def step5_verify_setup(access_token):
    """步驟 5：驗證設置"""
    print("🔍 步驟 5：驗證最終設置")
    print("-" * 40)
    
    try:
        # 檢查所有 resource subscriptions
        url = "https://api.gumroad.com/v2/resource_subscriptions"
        params = {'access_token': access_token}
        
        response = requests.get(url, params=params, timeout=30)
        result = response.json()
        
        if result.get('success'):
            subscriptions = result.get('resource_subscriptions', [])
            print(f"📋 目前共有 {len(subscriptions)} 個 webhook 訂閱:")
            
            for sub in subscriptions:
                print(f"  - {sub.get('resource_name')}: {sub.get('post_url')}")
                
            if len(subscriptions) >= 3:
                print("✅ Resource Subscriptions 設置完成")
            else:
                print("⚠️ Resource Subscriptions 設置可能不完整")
        else:
            print(f"❌ 無法驗證設置: {result}")
    
    except Exception as e:
        print(f"❌ 驗證設置時發生錯誤: {str(e)}")
    
    print()

def main():
    """主要設置流程"""
    print("🚀 Gumroad Webhook 完整設置指南")
    print("=" * 50)
    print()
    
    # 步驟 1：檢查環境
    access_token, webhook_secret, webhook_base_url = step1_check_environment()
    
    if not access_token:
        print("❌ 請先設置 GUMROAD_ACCESS_TOKEN")
        return
    
    if not webhook_secret:
        print("❌ 請先設置 GUMROAD_WEBHOOK_SECRET")
        return
    
    # 建構 webhook URL
    if not webhook_base_url:
        webhook_base_url = "https://scrilab.onrender.com"
    
    if not webhook_base_url.startswith('http'):
        webhook_base_url = f"https://{webhook_base_url}"
    
    webhook_url = f"{webhook_base_url.rstrip('/')}/gumroad/webhook"
    print(f"🔗 Webhook URL: {webhook_url}")
    print()
    
    # 詢問是否繼續
    confirm = input("確定要繼續設置嗎？(y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ 設置已取消")
        return
    
    print()
    
    # 步驟 2：移除舊設置
    step2_remove_ping_endpoint(access_token)
    
    # 步驟 3：設置新的 Resource Subscriptions
    success = step3_setup_resource_subscriptions(access_token, webhook_url)
    
    if success:
        # 步驟 4：測試
        step4_test_webhook(webhook_url, webhook_secret)
        
        # 步驟 5：驗證
        step5_verify_setup(access_token)
        
        print("🎉 設置完成！")
        print()
        print("接下來：")
        print("1. 重新部署您的應用")
        print("2. 進行一次測試購買")
        print("3. 檢查日誌確認簽名驗證成功")
    else:
        print("❌ 設置失敗，請檢查錯誤訊息")

if __name__ == "__main__":
    main()