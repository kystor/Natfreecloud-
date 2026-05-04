import time
import os
import base64
from seleniumbase import SB
import ddddocr

# ==========================================
# 1. 网站配置区域
# ==========================================
CONFIG = {
    "target_url": "https://nat.freecloud.ltd/login",
    "username_selector": "#emailInp",             
    "password_selector": "#emailPwdInp",          
    "captcha_img_selector": "#allow_login_email_captcha",          
    "captcha_input_selector": "#captcha_allow_login_email_captcha", 
    "login_btn_selector": 'button[type="submit"]'                  
}

# 提前创建一个文件夹，用来专门存放截图
os.makedirs("screenshots", exist_ok=True)

def take_screenshot(sb, step_name, username="system"):
    """截图辅助函数：自动给图片加上账号名和步骤编号"""
    safe_name = username.replace("@", "_").replace(".", "_")
    filepath = f"screenshots/{safe_name}_{step_name}.png"
    try:
        sb.save_screenshot(filepath)
        print(f"    📸 已截图保存: {filepath}")
    except Exception as e:
        print(f"    ⚠️ 截图失败 ({filepath}): {e}")

# ==========================================
# 2. 单个账号的处理流程（极简 CF 突破版）
# ==========================================
def process_single_account(username, password):
    print(f"\n==========================================")
    print(f"➡️ 开始处理账号: {username}")
    print(f"==========================================")
    
    # 核心：开启 uc 模式(反爬)，开启 xvfb 虚拟屏幕，强制走 Hysteria2 本地代理
    with SB(
        uc=True, 
        test=True, 
        locale="en", 
        xvfb=True, # 使用虚拟屏幕，这是在 Linux 服务器过 CF 的关键
        proxy="socks5://127.0.0.1:10808", 
        chromium_arg="--disable-blink-features=AutomationControlled,--window-size=1920,1080"
    ) as sb:
        print(f"🌐 正在访问目标网站: {CONFIG['target_url']}")
        
        # uc_open_with_reconnect 是专门用来对付 CF 全屏拦截（图一）的打开方式
        sb.uc_open_with_reconnect(CONFIG['target_url'], reconnect_time=6)
        time.sleep(3)
        take_screenshot(sb, "1_初始访问页面", username)

        # ----------------------------------------------------
        # 🛡️ 第一重验证：处理全屏 CF 拦截（如图一）
        # ----------------------------------------------------
        print("    🛡️ 尝试突破全屏 CF 验证...")
        try:
            # 这个原生命令会自动寻找 CF 框并用虚拟鼠标精准点击
            sb.uc_gui_click_captcha() 
            time.sleep(5) # 给网页留出跳转的时间
        except Exception:
            # 如果没找到框报错了也没关系，说明可能没遇到全屏拦截，继续往下走
            pass
            
        take_screenshot(sb, "2_全屏CF处理后状态", username)

        # ----------------------------------------------------
        # 🧩 第二重验证：处理内嵌 Turnstile 验证（如图二）
        # ----------------------------------------------------
        # 检查页面里有没有包含 turnstile 的 iframe
        if sb.is_element_present('iframe[src*="turnstile"]', timeout=3):
            print("    🧩 发现登录页内嵌的 CF 验证（如图二），尝试再次点击...")
            try:
                sb.uc_gui_click_captcha()
                time.sleep(4)
            except Exception:
                pass

        take_screenshot(sb, "3_内嵌CF处理后_准备填表", username)

        # ----------------------------------------------------
        # 📝 填写登录信息与图片验证码
        # ----------------------------------------------------
        try:
            print(">>> 正在提取 Base64 验证码数据...")
            # 等待图片验证码出现
            sb.wait_for_element(CONFIG['captcha_img_selector'], timeout=10)
            img_src = sb.get_attribute(CONFIG['captcha_img_selector'], "src")
            
            if "base64," in img_src:
                base64_data = img_src.split(',')[1]
                img_bytes = base64.b64decode(base64_data)
                
                # 识别图片验证码
                ocr = ddddocr.DdddOcr(show_ad=False)
                captcha_text = ocr.classification(img_bytes)
                print(f">>> 🤖 ddddocr 识别出的验证码为: {captcha_text}")
            else:
                print(">>> ⚠️ 错误：验证码图片的 src 不是 base64 格式，跳过此账号！")
                return

            print(">>> 正在输入账号、密码和验证码...")
            sb.type(CONFIG['username_selector'], username)
            sb.type(CONFIG['password_selector'], password)
            sb.type(CONFIG['captcha_input_selector'], captcha_text)

            take_screenshot(sb, "4_已填写数据准备登录", username)

            print(">>> 点击登录！")
            sb.click(CONFIG['login_btn_selector'])

            time.sleep(5)
            print(f"📄 登录后的页面标题是: {sb.get_title()}")
            take_screenshot(sb, "5_登录后的结果页面", username)
            print(f"✅ 账号 {username} 登录执行完毕！")

        except Exception as e:
            print(f"❌ 账号 {username} 处理过程中出现错误: {e}")
            take_screenshot(sb, "Error_程序崩溃截图", username)

# ==========================================
# 3. 主程序入口
# ==========================================
def main():
    print("🚀 自动化任务启动...")
    accounts_str = os.environ.get("acount")
    
    if not accounts_str:
        print("⚠️ 未获取到名为 'acount' 的环境变量，请检查 GitHub Secrets 配置！")
        return

    account_list = accounts_str.split(',')
    print(f"📋 共检测到 {len(account_list)} 个账号需要处理。")
    
    for item in account_list:
        item = item.strip()
        if ':' in item:
            parts = item.split(':', 1) 
            username = parts[0].strip()
            password = parts[1].strip()
            process_single_account(username, password)
        else:
            print(f"⚠️ 账号格式不正确（缺少冒号），已跳过: {item}")
            
    print("\n🏁 所有账号的队列任务已全部执行完成！")

if __name__ == "__main__":
    main()
