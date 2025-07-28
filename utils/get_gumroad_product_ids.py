#!/usr/bin/env python3
"""
get_gumroad_product_ids.py
快速獲取所有 Gumroad Product IDs 的腳本
"""
import requests
import json

def get_gumroad_products(access_token):
    """獲取所有 Gumroad 產品"""
    try:
        url = "https://api.gumroad.com/v2/products"
        data = {"access_token": access_token}
        
        response = requests.get(url, params=data)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get('success'):
            return result.get('products', [])
        else:
            print(f"❌ API 錯誤: {result}")
            return []
            
    except requests.RequestException as e:
        print(f"❌ 請求失敗: {str(e)}")
        return []
    except Exception as e:
        print(f"❌ 未知錯誤: {str(e)}")
        return []

def display_products(products):
    """顯示產品信息"""
    print("\n" + "="*80)
    print("📦 你的 Gumroad 產品列表")
    print("="*80)
    
    for i, product in enumerate(products, 1):
        print(f"\n🔹 產品 {i}:")
        print(f"   名稱: {product.get('name', 'Unknown')}")
        print(f"   價格: {product.get('formatted_price', 'N/A')}")
        print(f"   狀態: {'✅ 已發布' if product.get('published') else '❌ 未發布'}")
        print(f"   短網址: {product.get('short_url', 'N/A')}")
        print(f"   Permalink: {product.get('custom_permalink') or 'Auto-generated'}")
        print(f"   📋 Product ID: {product.get('id', 'N/A')}")
        print(f"   銷售數量: {product.get('sales_count', 0)}")

def generate_env_vars(products):
    """生成環境變數建議"""
    print("\n" + "="*80)
    print("🔧 建議的環境變數設置")
    print("="*80)
    
    # 根據產品名稱或價格自動分類
    trial_product = None
    monthly_product = None
    quarterly_product = None
    
    for product in products:
        name = product.get('name', '').lower()
        price_str = product.get('price', 0)
        
        # 嘗試根據名稱判斷
        if 'trial' in name or 'test' in name or '體驗' in name:
            trial_product = product
        elif 'quarter' in name or 'season' in name or '季' in name:
            quarterly_product = product
        elif 'month' in name or 'standard' in name or '標準' in name or '月' in name:
            monthly_product = product
        else:
            # 根據價格判斷
            if price_str <= 1000:  # $10 以下
                if not trial_product:
                    trial_product = product
            elif price_str <= 5000:  # $50 以下
                if not monthly_product:
                    monthly_product = product
            else:  # $50 以上
                if not quarterly_product:
                    quarterly_product = product
    
    print("# 建議的產品 ID 對應：")
    if trial_product:
        print(f"GUMROAD_TRIAL_PRODUCT_ID={trial_product['id']}")
        print(f"# ^ {trial_product['name']} ({trial_product.get('formatted_price', 'N/A')})")
    
    if monthly_product:
        print(f"GUMROAD_MONTHLY_PRODUCT_ID={monthly_product['id']}")
        print(f"# ^ {monthly_product['name']} ({monthly_product.get('formatted_price', 'N/A')})")
    
    if quarterly_product:
        print(f"GUMROAD_QUARTERLY_PRODUCT_ID={quarterly_product['id']}")
        print(f"# ^ {quarterly_product['name']} ({quarterly_product.get('formatted_price', 'N/A')})")
    
    # 顯示其他產品
    other_products = [p for p in products 
                     if p not in [trial_product, monthly_product, quarterly_product]]
    
    if other_products:
        print(f"\n# 其他產品：")
        for product in other_products:
            print(f"# {product['name']}: {product['id']}")
    
    print(f"\n# 總共 {len(products)} 個產品")

def main():
    print("🚀 Gumroad Product ID 獲取工具")
    print("="*50)
    
    # 獲取 Access Token
    access_token = input("請輸入你的 Gumroad Access Token: ").strip()
    
    if not access_token:
        print("❌ Access Token 不能為空")
        return
    
    if not access_token.startswith('gac_'):
        print("⚠️  警告: Access Token 通常以 'gac_' 開頭")
    
    print("\n🔍 正在獲取產品列表...")
    
    products = get_gumroad_products(access_token)
    
    if not products:
        print("❌ 未找到任何產品或獲取失敗")
        print("\n可能的原因:")
        print("1. Access Token 無效")
        print("2. 沒有創建任何產品")
        print("3. Token 權限不足（需要 'view_sales' 或 'edit_products' 權限）")
        return
    
    display_products(products)
    generate_env_vars(products)
    
    print(f"\n✅ 完成！共找到 {len(products)} 個產品")

if __name__ == "__main__":
    main()