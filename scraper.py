import os
import time
import random
import pandas as pd
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
# import undetected_chromedriver as uc
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

sys.stdout.reconfigure(encoding='utf-8')

# --------------------------
# LOGIN VIA USERNAME / PASSWORD
# --------------------------
def human_typing(element, text, delay_min=0.02, delay_max=0.14):
    for ch in text:
        element.send_keys(ch)
        time.sleep(random.uniform(delay_min, delay_max))

def login_with_credentials(driver, wait, username, password):
    try:
        driver.get("https://www.instagram.com/accounts/login/")
        # wait for username field
        user_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        pass_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))

        # clear and type with human-like delays
        user_input.clear()
        human_typing(user_input, username)
        time.sleep(random.uniform(0.5, 1.2))
        pass_input.clear()
        human_typing(pass_input, password)
        time.sleep(random.uniform(0.5, 1.0))

        # submit
        pass_input.send_keys(Keys.ENTER)

        # Wait for login success
        logged_in = False
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Search']"))
            )
            logged_in = True
        except Exception:
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//nav"))
                )
                logged_in = True
            except Exception:
                logged_in = False

        if logged_in:
            print("✅ Logged in via credentials")
            time.sleep(3)
            return True

        # Check for challenge / 2FA
        try:
            challenge = driver.find_elements(By.XPATH, "//*[contains(text(),'challenge') or contains(text(),'Confirm')]")
            if challenge:
                print("⚠️ Instagram challenge detected (checkpoint). Manual intervention required.")
                return False
        except Exception:
            pass

        if "two-factor" in driver.page_source.lower() or "two factor" in driver.page_source.lower():
            print("⚠️ Two-factor auth detected. Unable to proceed in fully automated mode.")
            return False

        print("⚠️ Login probably failed. Page title:", driver.title)
        driver.save_screenshot("login_failed.png")
        return False

    except Exception as e:
        print("⚠️ Exception during login:", e)
        driver.save_screenshot("login_exception.png")
        return False


def scrape_instagram(profile_url, start_date, end_date, username=None):
    # Generate output filename dynamically
    start_str = datetime.strptime(start_date, "%Y-%m-%d").strftime("%m-%d")
    end_str = datetime.strptime(end_date, "%Y-%m-%d").strftime("%m-%d")
    insta_user = profile_url.strip("/").split("/")[-1]
    output_file = f"{start_str}_{end_str}_{insta_user}.csv"

    # Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # PERFORMANCE OPTIMIZATIONS
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument("--disable-sync")
    chrome_options.add_argument("--metrics-recording-only")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_argument("--disable-translate")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-client-side-phishing-detection")
    chrome_options.add_argument("--disable-hang-monitor")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.managed_default_content_settings.javascript": 1,
        "profile.default_content_setting_values.cookies": 1,
        "profile.block_third_party_cookies": True,
    })

    # Initialize Chrome driver
    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 10)

    # LOGIN
    login_success = login_with_credentials(driver, wait, "adiadiadi1044", "Heybro@")
    if not login_success:
        driver.quit()
        return

    # Navigate to profile
    time.sleep(5)
    if not profile_url.startswith("http"):
        profile_url = f"https://www.instagram.com/{profile_url.strip().strip('/')}/"
    driver.get(profile_url)
    print("✅ Profile page loaded")
    time.sleep(5)

    # Click first post
    first_post_xpath = '/html/body/div[1]/div/div/div[2]/div/div/div[1]/div[2]/div[1]/section/main/div/div/div[2]/div/div/div/div/div[1]/div[1]/a'
    try:
        first_post = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, first_post_xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", first_post)
        time.sleep(5)
        driver.execute_script("arguments[0].click();", first_post)
        print("✅ Clicked first post")
        time.sleep(3)
    except Exception as e:
        print(f"⚠️ Error clicking first post: {e}")
        driver.save_screenshot("click_error.png")
        driver.quit()
        return

    # Scrape posts
    data = []
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    post_count = 0
    while True:
        post_count += 1
        print(f"\n📸 Scraping Post {post_count}")
        try:
            post_url = driver.current_url

            # Date
            try:
                date_element = driver.find_element(By.XPATH, '//time')
                datetime_str = date_element.get_attribute("datetime")
                datetime_obj = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
                date_posted = datetime_obj.strftime("%Y-%m-%d")
                time_posted = datetime_obj.strftime("%H:%M:%S")
            except NoSuchElementException:
                datetime_obj = None
                date_posted, time_posted = "Unknown", "Unknown"

            if post_count > 3 and datetime_obj and datetime_obj.date() < start_dt.date():
                print(f"🛑 Post {post_count} is older than start date. Stopping scrape.")
                break

            # Likes
            try:
                likes = driver.find_element(By.XPATH, '//section[2]/div/div/span/a/span/span').text
            except NoSuchElementException:
                likes = "Hidden"

            # Caption & comments
            all_comments_data = []
            if datetime_obj and start_dt.date() <= datetime_obj.date() <= end_dt.date():
                try:
                    comments_container = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '//ul/div/li/div/div/div[2]/div[1]/span'))
                    )
                    try:
                        caption_elem = driver.find_element(By.XPATH, '//div[@role="dialog"]//div[contains(@class,"C4VMK")]/span')
                        caption_text = caption_elem.text.strip()
                        all_comments_data.append(caption_text)
                        print(f"📝 Caption: {caption_text}")
                    except Exception:
                        pass
                    # Load comments
                    prev_count = 0
                    while True:
                        comment_blocks = comments_container.find_elements(By.XPATH, './li/div/div/div[2]/div[1]/span')
                        current_count = len(comment_blocks)
                        for comment_elem in comment_blocks[prev_count:]:
                            try:
                                comment_text = comment_elem.text.strip()
                                all_comments_data.append(comment_text)
                                print(f"💬 Comment: {comment_text}")
                            except Exception:
                                continue
                        if current_count == prev_count:
                            break
                        prev_count = current_count
                        try:
                            load_more_btn = comments_container.find_element(By.XPATH, './li/div/button')
                            driver.execute_script("arguments[0].click();", load_more_btn)
                            time.sleep(2)
                        except NoSuchElementException:
                            break
                except Exception:
                    print("⚠️ Comments div not found")
            else:
                print(f"⏭ Post {post_count} skipped: date {date_posted} not in range.")

            # Save post data
            first_row = True
            raw_caption = all_comments_data[0] if all_comments_data else ""
            if raw_caption:
                parts = raw_caption.split()
                hashtags = [p for p in parts if p.startswith("#")]
                caption_clean = " ".join(p for p in parts if not p.startswith("#"))
                hashtags_text = ", ".join(hashtags)
            else:
                caption_clean = ""
                hashtags_text = ""

            for comment in all_comments_data[1:]:
                data.append({
                    "username": profile_url.split("/")[-2],
                    "Post_Number": post_count,
                    "URL": post_url,
                    "Date": date_posted if first_row else "",
                    "Time": time_posted if first_row else "",
                    "Likes": likes if first_row else "",
                    "Caption": caption_clean if first_row else "",
                    "Hashtags": hashtags_text if first_row else "",
                    "Comments": comment,
                })
                first_row = False

            # Next post
            try:
                next_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//div[contains(@class, "_aaqg") and contains(@class, "_aaqh")]//button[contains(@class, "_abl-")]'))
                )
                driver.execute_script("arguments[0].click();", next_btn)
                time.sleep(random.uniform(3, 5))
            except TimeoutException:
                print("⚠️ Next button not found, stopping.")
                break

        except Exception as e:
            print(f"⚠️ Error scraping post {post_count}: {e}")
            continue

    # Save to CSV
    if data:
        df = pd.DataFrame(data)
        df.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"\n✅ Data saved to {output_file} (Rows: {len(df)})")
    else:
        print("\n⚠️ No data scraped.")

    driver.quit()
    print("\n✅ Scraping completed successfully!")


# -------------------------
# CLI Run (multi-profile, single output file)
# -------------------------
from concurrent.futures import ThreadPoolExecutor, as_completed
if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: python scraper.py <profile_url(s) comma-separated> <start_date> <end_date> <username> <artifact_name>")
        sys.exit(1)

    profiles_arg = sys.argv[1]
    start_date = sys.argv[2]
    end_date = sys.argv[3]
    username = sys.argv[4]
    artifact_name = sys.argv[5]

    profiles = [p.strip() for p in profiles_arg.split(",") if p.strip()]

    if not profiles:
        print("⚠️ No profiles provided.")
        sys.exit(1)

    combined_df = pd.DataFrame()

    def scrape_and_return_df(profile):
        try:
            scrape_instagram(profile, start_date, end_date, username)
            start_str = datetime.strptime(start_date, "%Y-%m-%d").strftime("%m-%d")
            end_str = datetime.strptime(end_date, "%Y-%m-%d").strftime("%m-%d")
            insta_user = profile.strip("/").split("/")[-1]
            temp_file = f"{start_str}_{end_str}_{insta_user}.csv"
            if os.path.exists(temp_file):
                temp_df = pd.read_csv(temp_file, encoding="utf-8-sig")
                os.remove(temp_file)
                return temp_df
        except Exception as e:
            print(f"⚠️ Error scraping {profile}: {e}")
        return pd.DataFrame()

    max_threads = min(5, len(profiles))
    with ThreadPoolExecutor(max_threads) as executor:
        futures = {executor.submit(scrape_and_return_df, profile): profile for profile in profiles}
        for future in as_completed(futures):
            profile = futures[future]
            try:
                df = future.result()
                if not df.empty:
                    combined_df = pd.concat([combined_df, df], ignore_index=True)
            except Exception as e:
                print(f"⚠️ Exception for {profile}: {e}")

    # Save combined CSV
    if not combined_df.empty:
        combined_df.to_csv(f"{artifact_name}.csv", index=False, encoding="utf-8-sig")
        print(f"\n✅ All profiles data combined and saved to {artifact_name}.csv (Rows: {len(combined_df)})")
    else:
        print("⚠️ No data scraped from any profile.")
