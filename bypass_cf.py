from seleniumbase import SB
import time

def main():
    print("🚀 开始执行 Cloudflare 突破脚本 (全过程排错截图版)...\n")
    
    # 1. 启动配置
    # uc=True: 开启隐藏模式 (Undetected ChromeDriver)，这是绕过 CF 的核心参数。
    # test=True: 在测试模式下运行，方便排查报错。
    # locale="zh-CN": 设置浏览器语言为中文。
    with SB(uc=True, test=True, locale="zh-CN", chromium_arg="--disable-blink-features=AutomationControlled") as sb:
        
        target_url = "https://nat.freecloud.ltd/login"
        print(f"🌐 步骤 1: 正在访问目标网站 -> {target_url}")
        
        # 2. 访问网页
        sb.uc_open_with_reconnect(target_url, reconnect_time=6)
        
        # 📸 【新增截图 1】：记录刚执行完打开网页命令后的瞬间状态。
        # 如果这里截图显示白屏或者网络错误，说明你的代理节点连通性有问题。
        sb.save_screenshot("01_after_open.png")
        print("  📸 已截图: 01_after_open.png (记录网页初始加载状态)")
        
        print("🛡️ 步骤 2: 正在等待并处理可能出现的全屏拦截盾...")
        # 等待 3 秒，让网页上的 CF 盾牌彻底加载出来
        time.sleep(3)
        
        # 📸 【新增截图 2】：记录等待 3 秒后的状态。
        # 正常情况下，这张图应该能看到 CF 的“验证你是人类”的复选框。
        sb.save_screenshot("02_wait_shield.png")
        print("  📸 已截图: 02_wait_shield.png (记录等待 CF 盾加载后的状态)")
        
        # 3. 尝试物理点击
        try:
            # 模拟真人的鼠标轨迹去点击屏幕上的验证框
            sb.uc_gui_click_captcha()
            print("  ↳ 🖱️ 已执行拟人化鼠标点击...")
            
            # 等待 1 秒钟，让点击的动画反馈出来
            time.sleep(1) 
            
            # 📸 【新增截图 3-A】：记录鼠标点击验证框之后的瞬间。
            # 这可以帮我们确认代码有没有点歪，或者 CF 盾有没有变成绿色的打勾状态。
            sb.save_screenshot("03_after_click.png")
            print("  📸 已截图: 03_after_click.png (记录点击验证框后的状态)")
            
        except Exception:
            print("  ↳ ℹ️ 未发现需要点击的验证框，可能正在无感通过...")
            
            # 📸 【新增截图 3-B】：如果代码报错说没找到框，截个图看看当前到底是什么界面。
            sb.save_screenshot("03_no_click_target.png")
            print("  📸 已截图: 03_no_click_target.png (记录未找到验证框时的页面状态)")
            
        print("⏳ 步骤 3: 正在等待网页跳转到登录页面...")
        
        # 故意等待 4 秒，观察验证通过后的中途跳转过程
        time.sleep(4)
        
        # 📸 【新增截图 4】：记录跳转过程中的状态。
        # CF 验证通过后，经常会有几秒钟的重定向白屏或加载动画。
        sb.save_screenshot("04_during_redirect.png")
        print("  📸 已截图: 04_during_redirect.png (记录跳转过程中的状态)")
        
        # 4. 验证是否成功
        target_element = 'input#emailInp[name="email"]'
        
        try:
            # 之前总共等了 15 秒，这里已经睡了 4 秒，所以剩下 11 秒超时判定
            sb.wait_for_element_visible(target_element, timeout=11)
            
            print("\n✅ 恭喜！成功突破拦截！")
            print("🎉 已经成功检测到目标邮箱输入框。")
            
            html_code = sb.get_attribute(target_element, "outerHTML")
            print(f"📄 抓取到的网页元素: \n{html_code}\n")
            
            # 📸 【新增截图 5-A】：大功告成，记录最终成功的登录页界面。
            sb.save_screenshot("05_success_page.png")
            print("  📸 已截图: 05_success_page.png (最终成功状态)")
            
        except Exception:
            print("\n❌ 失败：依然没有看到邮箱输入框。")
            
            # 📸 【新增截图 5-B】：如果最终依然失败，拍下死亡现场。
            # 这能让你知道是还在被拦截，还是跳转到了其他奇怪的页面。
            sb.save_screenshot("05_fail_page.png")
            print("  📸 已截图: 05_fail_page.png (最终失败状态)")

if __name__ == "__main__":
    main()
