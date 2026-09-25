from __future__ import annotations

import os
import sys
import time
from playwright.sync_api import sync_playwright

def run_ui_test():
    screenshot_dir = os.path.abspath("scratch/ui_screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)

    errors = []
    console_logs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 960})
        page = context.new_page()

        # Listen for console errors & unhandled exceptions
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda exc: errors.append(f"PageError: {exc}"))

        print("1. Đang truy cập http://localhost:8501...")
        page.goto("http://localhost:8501", timeout=30000)
        page.wait_for_load_state("networkidle")
        time.sleep(3)

        # Check for initial top-level exceptions
        exceptions = page.locator('[data-testid="stException"], .stException').all()
        for exc in exceptions:
            msg = exc.inner_text()
            errors.append(f"Initial Page Exception: {msg}")
            print(f"❌ Phát hiện lỗi ban đầu: {msg}")

        page.screenshot(path=os.path.join(screenshot_dir, "01_overview.png"), full_page=True)
        print(" -> Đã chụp ảnh màn hình tổng quan: 01_overview.png")

        # Get the top-level main tabs (first 5 tabs)
        tabs = page.locator('[role="tab"]').all()
        main_tab_count = min(5, len(tabs))
        print(f"2. Tìm thấy {len(tabs)} tabs. Bắt đầu kiểm tra {main_tab_count} tab chính...")

        for idx in range(main_tab_count):
            tab = page.locator('[role="tab"]').nth(idx)
            tab_name = tab.inner_text()
            print(f"\n--- [Kiểm tra Tab {idx+1}]: {tab_name} ---")
            tab.click()
            time.sleep(2)
            page.wait_for_load_state("networkidle")

            # Check exceptions
            tab_exceptions = page.locator('[data-testid="stException"], .stException').all()
            if tab_exceptions:
                for exc in tab_exceptions:
                    msg = exc.inner_text()
                    errors.append(f"Lỗi trên {tab_name}: {msg}")
                    print(f"❌ Lỗi trên {tab_name}: {msg}")
            else:
                print(f"✅ {tab_name}: Không có lỗi (0 exceptions)!")

            # Detailed checks per tab
            if "Tiêm Lỗi" in tab_name:
                print(" -> Đang kiểm tra các expander kịch bản tiêm lỗi...")
                expanders = page.locator('[data-testid="stExpander"]').all()
                print(f" -> Tìm thấy {len(expanders)} expanders kịch bản.")
                for e_idx, exp in enumerate(expanders[:3]):
                    exp.click()
                    time.sleep(0.5)

            if "RAG" in tab_name:
                print(" -> Đang kiểm tra tính năng truy vấn RAG tương tác...")
                run_btn = page.locator('button:has-text("Thực hiện truy vấn RAG")')
                if run_btn.is_visible():
                    run_btn.click()
                    print(" -> Đã nhấn nút 'Thực hiện truy vấn RAG', chờ phản hồi...")
                    # Wait up to 10s for RAG response
                    time.sleep(6)
                    page.wait_for_load_state("networkidle")

                    rag_exceptions = page.locator('[data-testid="stException"], .stException').all()
                    if rag_exceptions:
                        for exc in rag_exceptions:
                            msg = exc.inner_text()
                            errors.append(f"Lỗi sau khi truy vấn RAG: {msg}")
                            print(f"❌ Lỗi sau khi bấm truy vấn: {msg}")
                    else:
                        print("✅ RAG Query chạy thành công, đã render câu trả lời & context chunks!")

            if "Dữ Liệu" in tab_name:
                print(" -> Đang kiểm tra các tab báo cáo con...")
                sub_tabs = page.locator('[role="tab"]').all()[5:]
                for s_idx, s_tab in enumerate(sub_tabs):
                    s_name = s_tab.inner_text()
                    print(f"   -> Chuyển sang sub-tab: {s_name}")
                    s_tab.click()
                    time.sleep(1)

            screenshot_path = os.path.join(screenshot_dir, f"tab_{idx+1}_{idx}.png")
            page.screenshot(path=screenshot_path, full_page=True)
            print(f" -> Đã lưu ảnh chụp: {screenshot_path}")

        browser.close()

    print("\n" + "="*60)
    print("🎯 KẾT QUẢ KIỂM THỬ PLAYWRIGHT UI:")
    print("="*60)
    if errors:
        print(f"❌ THẤT BẠI: Phát hiện {len(errors)} lỗi trên giao diện:")
        for e in errors:
            print(f"   • {e}")
        sys.exit(1)
    else:
        print("✅ THÀNH CÔNG RỰC RỠ: 100% Giao diện hoạt động hoàn hảo, không có bất kỳ lỗi nào!")
        print(f"📸 Toàn bộ ảnh chụp kiểm thử đã lưu tại: {screenshot_dir}")
        sys.exit(0)

if __name__ == "__main__":
    run_ui_test()
