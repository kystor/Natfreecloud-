import time
import os
import base64
from seleniumbase import SB
import ddddocr

# ==========================================
# 1. 网站配置区域 (已更新为你提供的真实元素 ID)
# ==========================================
CONFIG = {
    "target_url": "https://nat.freecloud.ltd/login",
    "username_selector": "#emailInp",             # 【已更新】账号输入框 ID
    "password_selector": "#emailPwdInp",          # 【已更新】密码输入框 ID
    "captcha_img_selector": "#allow_login_email_captcha",          # 验证码图片
    "captcha_input_selector": "#captcha_allow_login_email_captcha", # 验证码输入框
    "login_btn_selector": 'button[type="submit"]'                  # 登录按钮
}

# ==========================================
# 2. Cloudflare 绕过辅助函数 (保持不变)
# ==========================================
def is_cloudflare_interstitial(sb) -> bool:
    try:
        page_source = sb.get_page_source()
        title = sb.get_title().lower() if sb.get_title() else ""
        indicators = ["Just a moment", "Verify you are human", "Checking your browser", "Checking if the site connection is secure"]
        for ind in indicators:
            if ind in page_source:
                return True
        if "just a moment" in title or "attention required" in title:
            return True
        body_len = sb.execute_script('(function() { return document.body ? document.body.innerText.length : 0; })();')
        if body_len is not None and body_len < 200 and "challenges.cloudflare.com" in page_source:
            return True
        return False
    except:
        return False

def bypass_cloudflare_interstitial(sb, max_attempts=3) -> bool:
    print("    🛡️ 检测到 CF 5秒盾，准备破除...")
    for attempt in range(max_attempts):
        print(f"      ▶ 尝试绕过 ({attempt+1}/{max_attempts})...")
        try:
            sb.uc_gui_click_captcha()
            time.sleep(6)
            if not is_cloudflare_interstitial(sb):
                print("      ✅ CF 5秒盾已通过！")
                return True
        except Exception as e:
            print(f"      ⚠️ 绕过异常: {e}")
        time.sleep(3)
    return False

def handle_turnstile_verification(sb) -> bool:
    try:
        cookie_btn = 'button[data-cky-tag="accept-button"]'
        if sb.is_element_visible(cookie_btn):
            print("    🍪 清理 Cookie 弹窗干扰...")
            sb.click(cookie_btn)
            time.sleep(1)
    except:
        pass

    sb.execute_script('''
        try {
            var t = document.querySelector('.cf-turnstile') || 
                    document.querySelector('iframe[src*="challenges.cloudflare"]') || 
                    document.querySelector('iframe[src*="turnstile"]');
            if (t) t.scrollIntoView({behavior:'smooth', block:'center'});
        } catch(e) {}
    ''')
    time.sleep(2)

    has_turnstile = False
    for _ in range(15):
        if (sb.is_element_present('iframe[src*="challenges.cloudflare"]') or 
            sb.is_element_present('iframe[src*="turnstile"]') or 
            sb.is_element_present('.cf-turnstile') or 
            sb.is_element_present('input[name="cf-turnstile-response"]')):
            has_turnstile = True
            break
        time.sleep(1)

    if not has_turnstile:
        print("    🟢 无感验证通过 (未发现 Turnstile)")
        return True

    print("    🧩 发现验证码，执行拟人点击...")
    verified = False
    
    for attempt in range(1, 4):
        print(f"      ▶ 点击尝试 ({attempt}/3)...")
        try:
            sb.uc_gui_click_captcha()
        except:
            pass
            
        for _ in range(10):
            if sb.is_element_present('input[name="cf-turnstile-response"]'):
                token = sb.get_attribute('input[name="cf-turnstile-response"]', 'value')
                if token and len(token) > 20:
                    print("      ✅ 物理点击成功，已获取 Token！")
                    verified = True
                    break
            time.sleep(1)
            
        if verified:
            break

    if not verified:
        print("    ⏳ 等待验证码自动计算 (最多30秒)...")
        for _ in range(30):
            if sb.is_element_present('input[name="cf-turnstile-response"]'):
                token = sb.get_attribute('input[name="cf-turnstile-response"]', 'value')
                if token and len(token) > 20:
                    print("      ✅ 验证码自动放行，已获取 Token！")
                    verified = True
                    break
            time.sleep(1)

    if not verified:
        print("    ❌ 验证失败，未获取有效 Token。")
        return False
        
    return True

# ==========================================
# 3. 单个账号的处理流程（封装成函数方便循环调用）
# ==========================================
def process_single_account(username, password):
    print(f"\n==========================================")
    print(f"➡️ 开始处理账号: {username}")
    print(f"==========================================")
    
    # 每次处理新账号，都启动一个全新的、干净的浏览器环境
    # 这样能避免上一个账号的 Cookie 缓存影响下一个账号
    # 部署在 GitHub 时，务必将 headless 设置为 True
    with SB(uc=True, test=True, locale="en", headless=True, chromium_arg="--disable-blink-features=AutomationControlled") as sb:
        print(f"🌐 正在访问目标网站: {CONFIG['target_url']}")
        sb.uc_open_with_reconnect(CONFIG['target_url'], reconnect_time=8)
        time.sleep(4)

        # ---------------- 第一关：过 Cloudflare 盾 ----------------
        if is_cloudflare_interstitial(sb):
            if not bypass_cloudflare_interstitial(sb):
                print(f"❌ 无法绕过 CF 整页拦截，跳过此账号。")
                return 
            time.sleep(3) 
            
        print(f"🛡️ 检查并处理页面内的 Turnstile 验证码...")
        handle_turnstile_verification(sb)
        
        print("🎉 CF 验证已处理完毕，即将进入图片验证码环节。")
        time.sleep(3) # 等待页面刷新或完全加载

        # ---------------- 第二关：识别 Base64 验证码并登录 ----------------
        try:
            print(">>> 正在提取 Base64 验证码数据...")
            sb.wait_for_element(CONFIG['captcha_img_selector'], timeout=10)
            img_src = sb.get_attribute(CONFIG['captcha_img_selector'], "src")
            
            if "base64," in img_src:
                base64_data = img_src.split(',')[1]
                img_bytes = base64.b64decode(base64_data)
                
                ocr = ddddocr.DdddOcr(show_ad=False)
                captcha_text = ocr.classification(img_bytes)
                print(f">>> 🤖 ddddocr 识别出的验证码为: {captcha_text}")
            else:
                print(">>> ⚠️ 错误：验证码图片的 src 不是 base64 格式，跳过此账号！")
                return

            # 填写登录信息
            print(">>> 正在输入账号、密码和验证码...")
            sb.type(CONFIG['username_selector'], username)
            sb.type(CONFIG['password_selector'], password)
            sb.type(CONFIG['captcha_input_selector'], captcha_text)

            # 点击登录
            print(">>> 点击登录！")
            sb.click(CONFIG['login_btn_selector'])

            time.sleep(5)
            print(f"📄 登录后的页面标题是: {sb.get_title()}")
            print(f"✅ 账号 {username} 执行完毕！")

        except Exception as e:
            print(f"❌ 账号 {username} 处理过程中出现错误: {e}")

# ==========================================
# 4. 主控程序：负责读取环境变量并循环分发任务
# ==========================================
def main():
    print("🚀 自动化任务启动...")
    
    # 1. 获取名为 acount 的环境变量
    # 如果没拿到，给一个本地测试用的默认格式
    accounts_str = os.environ.get("acount", "user1@abc.com:pass1,user2@abc.com:pass2")
    
    if not accounts_str:
        print("⚠️ 未获取到名为 'acount' 的环境变量，程序结束。")
        return

    # 2. 按照逗号将多个账号切分开
    # 例如："a:1,b:2" -> 变成列表 ['a:1', 'b:2']
    account_list = accounts_str.split(',')
    
    print(f"📋 共检测到 {len(account_list)} 个账号需要处理。")
    
    # 3. 使用 for 循环，排队处理每一个账号
    for item in account_list:
        item = item.strip() # 去掉前后多余的空格
        
        # 确保格式正确，包含冒号
        if ':' in item:
            # 按照第一个冒号进行切分，分为账号和密码两部分
            parts = item.split(':', 1) 
            username = parts[0].strip()
            password = parts[1].strip()
            
            # 调用上面的单账号处理流程
            process_single_account(username, password)
        else:
            print(f"⚠️ 账号格式不正确（缺少冒号），已跳过: {item}")
            
    print("\n🏁 所有账号的队列任务已全部执行完成！")

if __name__ == "__main__":
    main()
