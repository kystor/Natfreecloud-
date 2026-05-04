from seleniumbase import SB
import time

def main():
    print("🚀 开始执行 Cloudflare 突破脚本...\n")
    
    # 1. 启动配置
    # uc=True: 开启隐藏模式 (Undetected ChromeDriver)，这是绕过 CF 的核心参数。
    # test=True: 在测试模式下运行，方便排查报错。
    # locale="zh-CN": 设置浏览器语言为中文。
    with SB(uc=True, test=True, locale="zh-CN", chromium_arg="--disable-blink-features=AutomationControlled") as sb:
        
        target_url = "https://nat.freecloud.ltd/login"
        print(f"🌐 步骤 1: 正在访问目标网站 -> {target_url}")
        
        # 2. 访问网页
        # uc_open_with_reconnect 是专属绝招：它会在加载时主动断开并重连，
        # 这种方式能极大地提高通过 Cloudflare 初始 JS 质询的成功率。
        sb.uc_open_with_reconnect(target_url, reconnect_time=6)
        
        print("🛡️ 步骤 2: 正在等待并处理可能出现的全屏拦截盾...")
        # 等待 3 秒，让网页上的 CF 盾牌彻底加载出来
        time.sleep(3)
        
        # 3. 尝试物理点击
        try:
            # 模拟真人的鼠标轨迹去点击屏幕上的验证框
            sb.uc_gui_click_captcha()
            print("  ↳ 🖱️ 已执行拟人化鼠标点击...")
        except Exception:
            # 如果没找到框报错了，直接忽略。因为有时候 CF 会“无感通过”，不需要点击
            print("  ↳ ℹ️ 未发现需要点击的验证框，可能正在无感通过...")
            pass
            
        print("⏳ 步骤 3: 正在等待网页跳转到登录页面...")
        
        # 4. 验证是否成功
        # 你的成功标志：<input type="text" class="form-control" id="emailInp" name="email" ...>
        # 我们这里使用 CSS 选择器 'input#emailInp[name="email"]' 来精准定位它
        target_element = 'input#emailInp[name="email"]'
        
        try:
            # wait_for_element_visible：死死盯着屏幕，直到这个元素出现为止，最长等 15 秒
            sb.wait_for_element_visible(target_element, timeout=15)
            
            print("\n✅ 恭喜！成功突破拦截！")
            print("🎉 已经成功检测到目标邮箱输入框。")
            
            # 抓取并打印这个元素的 HTML 源代码，让你亲眼看到成果
            html_code = sb.get_attribute(target_element, "outerHTML")
            print(f"📄 抓取到的网页元素: \n{html_code}\n")
            
            # 可选：给成功的页面拍个照留作纪念，排查问题时也很有用
            sb.save_screenshot("success_page.png")
            print("📸 登录页面的截图已保存为: success_page.png")
            
        except Exception:
            # 如果等了 15 秒还没出现这个输入框，说明拦截突破失败了
            print("\n❌ 失败：等待了 15 秒，依然没有看到邮箱输入框。")
            print("📸 正在保存失败时的网页截图 (fail_page.png) 供你排查原因...")
            sb.save_screenshot("fail_page.png")

if __name__ == "__main__":
    main()
