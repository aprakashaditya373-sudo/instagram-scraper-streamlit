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
import json

sys.stdout.reconfigure(encoding='utf-8')

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
    
    # ------------------------
    # PERFORMANCE OPTIMIZATIONS
    # ------------------------
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
        "profile.default_content_setting_values.images": 2,  # disable images
        "profile.managed_default_content_settings.stylesheets": 2,  # disable CSS
        "profile.managed_default_content_settings.javascript": 1,  # keep JS for functionality
        "profile.default_content_setting_values.cookies": 1,
        "profile.block_third_party_cookies": True,
    })

    # Initialize Chrome driver
    service = Service()  # Add path if chromedriver not in PATH
    driver = webdriver.Chrome(service=service, options=chrome_options)
    # driver = uc.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)

    # Open Instagram main page
    driver.get("https://www.instagram.com/")
    print("🔄 Opening Instagram...")
    time.sleep(5)

    # ------------------------
    # Login via hardcoded cookies
    # ------------------------
    try:
        cookies = [
            {"name": "csrftoken", "value": "Rf5IkDkC5ToB7WLxwBJXqBsEhhtacnYH", "domain": ".instagram.com", "path": "/"},
            {"name": "datr",      "value": "BYzwaMODPk1FrOWDRvKdP-MI", "domain": ".instagram.com", "path": "/"},
            {"name": "dpr",       "value": "1.25", "domain": ".instagram.com", "path": "/"},
            {"name": "ds_user_id","value": "72782729777", "domain": ".instagram.com", "path": "/"},
            {"name": "ig_did",    "value": "356B55F2-C173-46CA-BF6B-B6A34260D7AD", "domain": ".instagram.com", "path": "/"},
            {"name": "mid",       "value": "aPCMBQALAAEuhO8RpUZ7vfEg8cCZ", "domain": ".instagram.com", "path": "/"},
            {"name": "rur",       "value": "CCO\\05472782729777\\0541792582265:01fed7f09310a7dd37f9fec22286bbc198afe6145f400200f80c6c0eb422bfcb5d3356d9", "domain": ".instagram.com", "path": "/"},
            {"name": "sessionid", "value": "72782729777%3AXy000Mrq0Qnon7%3A3%3AAYgxnnMw8vAY39iGTTPeI3eoN9hZkwUZ4HKEP3my2A", "domain": ".instagram.com", "path": "/"},
            {"name": "wd",        "value": "679x730", "domain": ".instagram.com", "path": "/"},
        ]

        for cookie in cookies:
            driver.add_cookie(cookie)

        driver.refresh()
        time.sleep(5)
        print("✅ Logged in via hardcoded cookies, no CAPTCHA!")
    except Exception as e:
        print(f"⚠️ Error loading cookies: {e}")
        driver.quit()
        return

    # Navigate to profile
    time.sleep(5)
    # ✅ Normalize profile input
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
                    if post_count == 1:
                        try:
                            comments_container = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.XPATH, '/html/body/div[5]/div[1]/div/div[3]/div/div/div/div/div[2]/div/article/div/div[2]/div/div/div[2]/div[1]/ul/div[3]/div/div'))
                            )
                            caption_elem = comments_container.find_element(By.XPATH, '/html/body/div[5]/div[1]/div/div[3]/div/div/div/div/div[2]/div/article/div/div[2]/div/div/div[2]/div[1]/ul/div[1]/li/div/div/div[2]/div[1]/h1')
                        except Exception:
                            comments_container = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.XPATH, '/html/body/div[4]/div[1]/div/div[3]/div/div/div/div/div[2]/div/article/div/div[2]/div/div/div[2]/div[1]/ul/div[3]/div/div'))
                            )
                            caption_elem = comments_container.find_element(By.XPATH, '/html/body/div[4]/div[1]/div/div[3]/div/div/div/div/div[2]/div/article/div/div[2]/div/div/div[2]/div[1]/ul/div[1]/li/div/div/div[2]/div[1]/h1')
                    else:
                        try:
                            comments_container = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.XPATH, '/html/body/div[4]/div[1]/div/div[3]/div/div/div/div/div[2]/div/article/div/div[2]/div/div/div[2]/div[1]/ul/div[3]/div/div'))
                            )
                            caption_elem = comments_container.find_element(By.XPATH, '/html/body/div[4]/div[1]/div/div[3]/div/div/div/div/div[2]/div/article/div/div[2]/div/div/div[2]/div[1]/ul/div[1]/li/div/div/div[2]/div[1]/h1')
                        except Exception:
                            comments_container = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.XPATH, '/html/body/div[5]/div[1]/div/div[3]/div/div/div/div/div[2]/div/article/div/div[2]/div/div/div[2]/div[1]/ul/div[3]/div/div'))
                            )
                            caption_elem = comments_container.find_element(By.XPATH, '/html/body/div[5]/div[1]/div/div[3]/div/div/div/div/div[2]/div/article/div/div[2]/div/div/div[2]/div[1]/ul/div[1]/li/div/div/div[2]/div[1]/h1')

                    print(f"✅ Comments container found for Post {post_count}")
                    # Caption
                    try:
                        # caption_elem = comments_container.find_element(By.XPATH, '/html/body/div[4]/div[1]/div/div[3]/div/div/div/div/div[2]/div/article/div/div[2]/div/div/div[2]/div[1]/ul/div[1]/li/div/div/div[2]/div[1]/h1')
                        caption_text = caption_elem.text.strip()
                        all_comments_data.append(caption_text)
                        print(f"📝 Caption: {caption_text}")
                    except NoSuchElementException:
                        pass

                    # Load comments
                    prev_count = 0
                    while True:
                        comment_blocks = comments_container.find_elements(By.XPATH, './div[position()>=0]/ul/div/li/div/div/div[2]/div[1]/span')
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

            # Save post data (added hashtag separation here)
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
                next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[contains(@class, "_aaqg") and contains(@class, "_aaqh")]//button[contains(@class, "_abl-")]')))
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

from concurrent.futures import ThreadPoolExecutor, as_completed
if __name__ == "__main__":
    import sys
    import os

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
