import os
import sys
import re
import time
import random
import urllib.request
import json
import subprocess
import openpyxl

CURRENT_VERSION = "1.0.1"
GITHUB_REPO = "khoathoiloi/shorten-link-automation"

# Đảm bảo hiển thị Tiếng Việt trên Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
    except Exception:
        pass

from playwright.sync_api import sync_playwright

TARGET_URL = "https://shorten-link-swart.vercel.app/"

if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
    CURRENT_EXE = sys.executable
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    CURRENT_EXE = None

USER_DATA_DIR = os.path.join(APP_DIR, "user_data")

def is_newer_version(latest, current):
    try:
        l_parts = [int(p) for p in latest.split('.')]
        c_parts = [int(p) for p in current.split('.')]
        return l_parts > c_parts
    except Exception:
        return latest != current

def perform_update(download_url, new_version):
    """Tải file exe mới và tự động thay thế file cũ"""
    if not CURRENT_EXE:
        print(f"⚠️ Bạn đang chạy mã nguồn Python. Vui lòng tải file exe tại: {download_url}")
        return

    print(f"\n⏳ Đang tải bản cập nhật v{new_version}...")
    new_exe_path = CURRENT_EXE + ".new"
    
    def reporthook(blocknum, blocksize, totalsize):
        read = blocknum * blocksize
        if totalsize > 0:
            percent = min(100, int(read * 100 / totalsize))
            mb_read = read / (1024 * 1024)
            mb_total = totalsize / (1024 * 1024)
            sys.stdout.write(f"\r📥 Đang tải: {percent}% ({mb_read:.1f}MB / {mb_total:.1f}MB)")
            sys.stdout.flush()

    try:
        urllib.request.urlretrieve(download_url, new_exe_path, reporthook)
        print("\n✅ Tải về hoàn tất! Đang khởi động lại ứng dụng...")
        
        bat_script = f"""@echo off
timeout /t 2 /nobreak > nul
move /y "{new_exe_path}" "{CURRENT_EXE}"
start "" "{CURRENT_EXE}"
del "%~f0"
"""
        updater_bat = os.path.join(APP_DIR, "updater.bat")
        with open(updater_bat, "w", encoding="utf-8") as f:
            f.write(bat_script)
            
        subprocess.Popen(["cmd.exe", "/c", updater_bat], close_fds=True)
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Lỗi khi tự động cập nhật: {e}")
        print(f"👉 Bạn có thể tải thủ công tại: {download_url}")
        if os.path.exists(new_exe_path):
            try: os.remove(new_exe_path)
            except: pass

def check_for_updates():
    """Tự động kiểm tra bản cập nhật mới nhất từ GitHub Releases"""
    try:
        print("🔍 Đang kiểm tra bản cập nhật mới...", flush=True)
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        req = urllib.request.Request(url, headers={"User-Agent": "ShiftLink-App"})
        with urllib.request.urlopen(req, timeout=4) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                latest_tag = data.get("tag_name", "").lstrip("v")
                body = data.get("body", "Không có ghi chú cập nhật.")
                
                download_url = None
                for asset in data.get("assets", []):
                    if asset.get("name", "").endswith(".exe"):
                        download_url = asset.get("browser_download_url")
                        break

                if latest_tag and is_newer_version(latest_tag, CURRENT_VERSION) and download_url:
                    print("\n" + "=" * 65)
                    print(f"🎉 ĐÃ CÓ PHIÊN BẢN MỚI: v{latest_tag} (Phiên bản hiện tại: v{CURRENT_VERSION})")
                    print(f"📝 Nội dung mới:\n{body}")
                    print("=" * 65)
                    
                    choice = input("👉 Bạn có muốn tự động cập nhật ngay bây giờ không? (y/n, mặc định y): ").strip().lower()
                    if choice in ['', 'y', 'yes']:
                        perform_update(download_url, latest_tag)
                else:
                    print(f"✅ Bạn đang sử dụng phiên bản mới nhất (v{CURRENT_VERSION}).\n", flush=True)
    except Exception:
        pass

def wait_for_user_login(page):
    """Kiểm tra và chờ người dùng đăng nhập (không giới hạn thời gian)"""
    time.sleep(1.5)
    
    # Kiểm tra ngay
    user_profile = page.locator("#user-profile")
    user_display_name = page.locator("#user-display-name")
    profile_classes = user_profile.get_attribute("class") or ""
    
    if user_profile.is_visible() and "hidden" not in profile_classes:
        username = user_display_name.inner_text().strip() or "User"
        print(f"👤 Tài khoản đã đăng nhập sẵn: {username}")
        return True

    print("\n" + "-" * 65)
    print("⚠️ CHƯA ĐĂNG NHẬP!")
    print("👉 Xin mời bạn đăng ký / đăng nhập trực tiếp trên cửa sổ Chrome vừa mở...")
    print("⏳ Hệ thống đang chờ bạn đăng nhập (Không giới hạn thời gian)...")
    print("-" * 65)

    waited_seconds = 0
    while True:
        time.sleep(1)
        waited_seconds += 1
        
        try:
            # Kiểm tra xem người dùng có vô tình tắt trình duyệt không
            if page.is_closed():
                print("\n❌ Bạn đã đóng trình duyệt Chrome. Dừng chương trình.")
                return False
                
            p_classes = user_profile.get_attribute("class") or ""
            if user_profile.is_visible() and "hidden" not in p_classes:
                username = user_display_name.inner_text().strip() or "User"
                print(f"\n🎉 ĐĂNG NHẬP THÀNH CÔNG! Chào mừng {username}.")
                return True
        except Exception:
            pass

        # Hiển thị số giây đã đợi
        if waited_seconds % 2 == 0:
            mins, secs = divmod(waited_seconds, 60)
            time_str = f"{mins:02d}:{secs:02d}" if mins > 0 else f"{secs}s"
            sys.stdout.write(f"\r⏳ Đang đợi bạn đăng nhập trên Chrome... ({time_str})")
            sys.stdout.flush()

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

        # Kiểm tra và chờ đăng nhập linh hoạt (không giới hạn thời gian)
        if not wait_for_user_login(page):
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
    print(f"   CÔNG CỤ TỰ ĐỘNG HÓA RÚT GỌN LINK SHIFTLINK (v{CURRENT_VERSION})   ")
    print("*" * 65)
    
    check_for_updates()

    excel_path = input("👉 Kéo thả file Excel vào đây (hoặc dán đường dẫn): ").strip('\'"')
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
