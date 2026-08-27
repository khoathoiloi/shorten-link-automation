import os
import sys
import re
import time
import random
import openpyxl

# Đảm bảo hiển thị Tiếng Việt trên Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
    except Exception:
        pass

from playwright.sync_api import sync_playwright

TARGET_URL = "https://shorten-link-swart.vercel.app/"

# Lấy thư mục chạy để lưu user_data cạnh file exe
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

USER_DATA_DIR = os.path.join(APP_DIR, "user_data")

def extract_links_and_col(excel_path):
    wb = openpyxl.load_workbook(excel_path)
    sheet = wb['BaiDang'] if 'BaiDang' in wb.sheetnames else wb.active
    
    best_col = None
    max_links = 0
    for col in range(1, sheet.max_column + 1):
        link_count = 0
        for row in range(2, min(50, sheet.max_row + 1)):
            val = str(sheet.cell(row=row, column=col).value or '')
            if re.search(r'https?://[^\s]+', val):
                link_count += 1
        if link_count > max_links:
            max_links = link_count
            best_col = col

    if not best_col:
        return None, None, None, []

    col_name = sheet.cell(1, best_col).value or f"Cột {best_col}"
    print(f"\n🔍 [TỰ ĐỘNG NHẬN DIỆN]: Cột chứa link gốc là Cột {best_col} [{col_name}]", flush=True)

    links = []
    for r in range(2, sheet.max_row + 1):
        cell_val = str(sheet.cell(row=r, column=best_col).value or '')
        match = re.search(r'https?://[^\s]+', cell_val)
        if match:
            links.append((r, match.group(0), cell_val))
            
    return wb, sheet, best_col, links

def generate_short_slug(original_url, attempt=0):
    slug_part = re.sub(r'^https?://[^/]+(?:/[^/]+)*/', '', original_url.rstrip('/'))
    target_len = random.randint(15, 21)
    
    collected_chars = []
    char_count = 0
    for ch in reversed(slug_part):
        collected_chars.append(ch)
        if ch != '-':
            char_count += 1
        if char_count >= target_len:
            break
            
    result = ''.join(reversed(collected_chars))
    result = re.sub(r'^[^a-zA-Z0-9]+', '', result)
    result = re.sub(r'[^a-zA-Z0-9]+$', '', result)
    
    if attempt > 1:
        suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=2))
        result = f"{result[:18]}-{suffix}"
        
    return result

def run_automation(excel_path, selected_domain="nextpart2.online", max_items=None):
    excel_path = excel_path.strip('\'"')
    if not os.path.exists(excel_path):
        print(f"❌ Lỗi: Không tìm thấy file Excel tại '{excel_path}'", flush=True)
        return False

    wb, sheet, link_col, links = extract_links_and_col(excel_path)
    if not links:
        print("❌ Lỗi: Không tìm thấy đường link nào trong file Excel!", flush=True)
        return False

    # Tìm hoặc tạo cột "Link da rut gon"
    out_col = None
    for c in range(1, sheet.max_column + 1):
        if str(sheet.cell(1, c).value or '').strip().lower() == "link da rut gon":
            out_col = c
            break
    if not out_col:
        out_col = sheet.max_column + 1
        sheet.cell(row=1, column=out_col, value="Link da rut gon")

    items = links[:max_items] if max_items else links
    total = len(items)
    print(f"📊 Bắt đầu xử lý: {total} dòng dữ liệu...", flush=True)
    print("=" * 65, flush=True)

    url_cache = {}

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            channel="chrome",
            headless=False,
            args=["--start-maximized"],
            no_viewport=True
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(TARGET_URL, wait_until="domcontentloaded")
        time.sleep(1.5)

        # Kiểm tra đăng nhập
        user_profile = page.locator("#user-profile")
        profile_classes = user_profile.get_attribute("class") or ""
        if not (user_profile.is_visible() and "hidden" not in profile_classes):
            print("\n⚠️ CHƯA ĐĂNG NHẬP! Vui lòng đăng nhập trên cửa sổ Chrome...", flush=True)
            try:
                page.wait_for_selector("#user-profile:not(.hidden)", timeout=300000)
                print("✅ Đăng nhập thành công!", flush=True)
            except Exception:
                print("❌ Hết thời gian chờ đăng nhập (5 phút).", flush=True)
                context.close()
                return False

        for i, (row_idx, original_url, full_cell_text) in enumerate(items, start=1):
            if original_url in url_cache:
                cached_val = url_cache[original_url]
                sheet.cell(row=row_idx, column=out_col, value=cached_val)
                print(f"[{i:03d}/{total:03d}] Dòng #{row_idx:<3d} -> ⚡ [DÙNG LẠI] {cached_val}", flush=True)
                continue

            success = False
            for attempt in range(5):
                slug = generate_short_slug(original_url, attempt=attempt)
                
                page.locator("#original-url").fill(original_url)
                page.locator("#domain-select").select_option(label=selected_domain)
                page.locator("#short-path").fill(slug)

                try:
                    with page.expect_response(lambda res: "/api/links" in res.url and res.request.method == "POST", timeout=10000) as resp_info:
                        page.locator("#shorten-form button[type='submit']").click()

                    response = resp_info.value
                    if response.status in [200, 201]:
                        res_data = response.json()
                        created_path = res_data.get("shortPath", slug)
                        shortened_url = f"https://{selected_domain}/{created_path}"
                        final_text = f"watch full here 👉: {shortened_url}"
                        
                        url_cache[original_url] = final_text
                        sheet.cell(row=row_idx, column=out_col, value=final_text)
                        print(f"[{i:03d}/{total:03d}] Dòng #{row_idx:<3d} -> 🌐 [RÚT GỌN] {final_text}", flush=True)
                        success = True
                        break
                    else:
                        time.sleep(0.5)
                except Exception:
                    time.sleep(0.5)

            if not success:
                print(f"[{i:03d}/{total:03d}] Dòng #{row_idx:<3d} -> ⚠️ Thất bại sau 5 lần thử.", flush=True)

            time.sleep(0.6)

        context.close()

    # Lưu ra file mới
    dir_name = os.path.dirname(excel_path)
    base_name = os.path.splitext(os.path.basename(excel_path))[0]
    out_file = os.path.join(dir_name, f"{base_name}_rutgon.xlsx")
    wb.save(out_file)

    print("=" * 65, flush=True)
    print("🎉 HOÀN TẤT TẤT CẢ DÒNG DỮ LIỆU!", flush=True)
    print(f"💾 File kết quả đã lưu tại: {out_file}", flush=True)
    return True

def main():
    print("*" * 65)
    print("       CÔNG CỤ TỰ ĐỘNG HÓA RÚT GỌN LINK SHIFTLINK       ")
    print("*" * 65)
    
    excel_path = input("\n👉 Kéo thả file Excel vào đây (hoặc dán đường dẫn): ").strip('\'"')
    if not excel_path:
        default_file = r"C:\Users\TP\Desktop\blogbio-20260826-170943.xlsx"
        if os.path.exists(default_file):
            print(f"Sử dụng file mặc định: {default_file}")
            excel_path = default_file
        else:
            print("❌ Vui lòng nhập đường dẫn file Excel hợp lệ!")
            input("\nNhấn Enter để thoát...")
            return

    domain = input("👉 Chọn tên miền (Nhấn Enter để dùng mặc định: nextpart2.online): ").strip()
    if not domain:
        domain = "nextpart2.online"

    limit_str = input("👉 Số lượng dòng muốn xử lý (Nhấn Enter để xử lý TOÀN BỘ file): ").strip()
    limit = int(limit_str) if limit_str.isdigit() else None

    run_automation(excel_path, selected_domain=domain, max_items=limit)

    print("\n" + "=" * 65)
    input("👉 Nhấn phím Enter để kết thúc...")

if __name__ == "__main__":
    main()
