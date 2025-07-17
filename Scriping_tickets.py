import os
import time
import json
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException

# ✅ 参数配置
departure_code = "IST"
contients = ["Africa", "Asia", "Europe", "North America", "South America", "Oceania"]
selected_continents = [contients[0], contients[1], contients[2], contients[3], contients[5]]  # 选择所有大洲
file_path = 'Fly_Across_6_Continents.xlsx'
departure_date_label = "Thu Sep 04 2025"

# ✅ 读取数据
df_countries = pd.read_excel(file_path, sheet_name='turkish_countries')
df_airports = pd.read_excel(file_path, sheet_name='turkish_airports')

country_list = []
for continent in selected_continents:
    if continent in df_countries.columns:
        country_list.extend(df_countries[continent].dropna().tolist())

target_airports = df_airports[df_airports['country'].isin(country_list)]['airport_code'].dropna().unique().tolist()

# ✅ 随机 User-Agent 列表
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
]

# ✅ 创建截图文件夹
os.makedirs("screenshots", exist_ok=True)

# ✅ 初始化CSV文件
csv_file = f"turkish_prices_results_from_{departure_code}.csv"
if not os.path.exists(csv_file):
    pd.DataFrame(columns=[
        "departure", "arrival", "arrival_country", "arrival_continent",
        "date", "prices", "lowest_price_today", "week_prices", "lowest_price_week"
    ]).to_csv(csv_file, index=False)

# ✅ 模拟用户行为
def simulate_user_behavior(driver):
    time.sleep(random.uniform(1.2, 2.5))
    action = ActionChains(driver)
    for _ in range(random.randint(2, 5)):
        x = random.randint(50, 400)
        y = random.randint(50, 300)
        action.move_by_offset(x, y).perform()
        time.sleep(random.uniform(0.2, 0.5))
        action.reset_actions()

# ✅ 初始化浏览器
def init_driver():
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"user-agent={random.choice(user_agents)}")
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(random.randint(1280, 1600), random.randint(800, 1000))
    return driver

# ✅ 设置机场代码
def set_airport_code(driver, wait, input_id: str, airport_code: str):
    # 点击输入框并清空
    input_box = wait.until(EC.element_to_be_clickable((By.ID, input_id)))
    input_box.click()
    time.sleep(0.2)
    input_box.send_keys(Keys.CONTROL + "a")
    input_box.send_keys(Keys.DELETE)
    time.sleep(0.1)

    # 输入代码
    input_box = wait.until(EC.element_to_be_clickable((By.ID, input_id)))
    input_box.click()
    time.sleep(0.2)
    input_box.send_keys(airport_code)
    time.sleep(1.5)  # 等待下拉框出现

    # 获取下拉选项
    suggestions = wait.until(EC.presence_of_all_elements_located(
        (By.CSS_SELECTOR, 'ul[role="listbox"] > li[role="button"]')
    ))

    # 遍历查找匹配项
    found = False
    for suggestion in suggestions:
        try:
            code_span = suggestion.find_element(By.CSS_SELECTOR, 'span.hm__style_booker-input-list-item-text-code__bHpVL')
            code_text = code_span.text.strip('(), ')
            if code_text.upper() == airport_code.upper():
                driver.execute_script("arguments[0].scrollIntoView(true);", suggestion)
                driver.execute_script("arguments[0].click();", suggestion)
                print(f"✅ 选择了目标机场: {code_text}")
                found = True
                break
        except Exception as e:
            print(f"⚠️ 检查候选项时出错: {e}")
            continue

    # 如果没有找到匹配的，就选择第一个
    if not found:
        print("⚠️ 未找到完全匹配的机场代码，选择默认第一个。")
        driver.execute_script("arguments[0].click();", suggestions[0])

# ✅ 选择日期（支持跨月份导航）
def select_departure_date(driver, wait, label_str, max_months=6):
    date_area = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.hm__RoundAndOneWayTab_datePassengerArea__jToT9")))
    driver.execute_script("arguments[0].click();", date_area)
    time.sleep(1.5)
    
    # 循环查找日期，支持跨月份
    for month_count in range(max_months):
        spans = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'button span[aria-label]')))
        
        # 在当前页面查找目标日期
        for span in spans:
            if span.get_attribute("aria-label").strip() == label_str:
                button = span.find_element(By.XPATH, "./ancestor::button")
                driver.execute_script("arguments[0].click();", button)
                print(f"✅ 日期选择成功: {label_str}")
                return
        
        # 如果当前页面没找到，且不是最后一次尝试，则点击下个月
        if month_count < max_months - 1:
            try:
                # 查找下个月按钮，尝试多种选择器
                next_button = None
                selectors = [
                    "button.react-calendar__navigation__next-button",
                    "button[aria-label*='next']",
                    "button[aria-label*='Go to the next month']"
                ]
                
                for selector in selectors:
                    try:
                        next_button = driver.find_element(By.CSS_SELECTOR, selector)
                        break
                    except:
                        continue
                
                if next_button and next_button.is_enabled():
                    driver.execute_script("arguments[0].click();", next_button)
                    print(f"📅 切换到下个月 ({month_count + 2}/{max_months})")
                    time.sleep(1.5)
                else:
                    print("❌ 未找到可用的下个月按钮")
                    break
                    
            except Exception as e:
                print(f"❌ 切换月份时出错: {e}")
                break
    
    raise Exception(f"❌ 在 {max_months} 个月内未找到日期: {label_str}")

def wait_and_capture_prices(driver, wait, screenshot_name):
    try:
        # If modal showing no flights appears, skip
        try:
            WebDriverWait(driver, 6).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[id*="ForceRedirectBaseModal"]'))
            )
            print("⚠️ 当前无可用航班，已跳过截图与解析。")
            return []
        except TimeoutException:
            pass

        # Wait for flight list to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class*="av__FlightPanel_flightList__gxfmQ"]'))
        )
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class*="av__FlightItem_flightItem__BGnIP"]'))
        )
        time.sleep(1.2)

        # Click the filter button
        try:
            buttons = driver.find_elements(By.CSS_SELECTOR, 'div#directAndConnectingFilterDropdown')
            button = next(
                (btn for btn in buttons if "airline" in btn.text.strip().lower()), 
                None
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", button)
            button.click()
            time.sleep(0.5)
            print("🖱️ 已点击展开按钮。")
        except Exception as e:
            print(f"⚠️ 点击展开按钮失败: {e}")

        # Uncheck specific airlines
        try:
            targets = driver.find_elements(By.CSS_SELECTOR, "div.av__style_group__kbhRb.av__style_checkbox__XMtFs")

            for target in targets:
                label_elem = target.find_element(By.CSS_SELECTOR, 'label')
                label_text = label_elem.text.strip()

                if label_text == '':
                    continue

                if "turkish airlines" not in label_text.lower():
                    # 找到这个 div 里的按钮并点击 uncheck
                    checkbox_button = target.find_element(By.CSS_SELECTOR, 'button')
                    driver.execute_script("arguments[0].scrollIntoView(true);", checkbox_button)
                    checkbox_button.click()
                    time.sleep(0.3)

            print("✅ 已取消两个筛选条件。")
        except Exception as e:
            print(f"⚠️ 取消筛选条件时出错: {e}")

        # Check if there are any flights left
        time.sleep(1)
        price_blocks = driver.find_elements(By.CSS_SELECTOR, 'div[class*="av__FlightItem_flightItem__BGnIP"]')
        if not price_blocks:
            print("🚫 过滤后无航班结果，跳过记录。")
            return []

        # Extract economy prices
        economy_prices = []
        for block in price_blocks:
            try:
                price_info = block.find_element(By.CSS_SELECTOR, 'span[class*="av__style_price-type-content__3xWFY"]').text.strip()
                price_lines = price_info.split("\n")
                currency = price_lines[0].strip()
                price = "".join(price_lines[1:]).strip().replace(" ", "").replace(",", "")
                economy_prices.append({
                    "price": price,
                    "currency": currency
                })
            except:
                continue


        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)

        # 全屏 + 缩放
        driver.execute_script("""
            document.body.style.zoom = "75%";
        """)
        time.sleep(0.3)  # 等待渲染

        driver.save_screenshot(screenshot_name)
        print(f"📸 已截图：{screenshot_name}")

        # 🆕 If we have at least one economy price, fetch weekly calendar prices too
        if economy_prices:
            try:
                print("🔎 开始提取一周价格信息…")
                week_prices = []
                week_items = driver.find_elements(By.CSS_SELECTOR, 'li.av__style_clickable__WDRZn.av__style_chart-item__ZV7sq')
                for item in week_items:
                    try:
                        day = item.find_element(By.CSS_SELECTOR, 'span.av__style_number__Ld_TQ').text.strip()
                        month = item.find_element(By.CSS_SELECTOR, 'span.av__style_month__q39Dw').text.strip()
                        weekday = item.find_element(By.CSS_SELECTOR, 'span.av__style_dayname__Tm8AA').text.strip()
                        price_text = item.find_element(By.CSS_SELECTOR, 'span.av__style_pricePart__lYxno').text.strip().replace(",", "").replace(" ", "")
                        currency = item.find_element(By.CSS_SELECTOR, 'span.av__style_currency__9Z11P').text.strip().replace(",", "").replace(" ", "")
                        week_prices.append({
                            "date": f"{day} {month} ({weekday})",
                            "price": price_text,
                            "currency": currency
                        })
                    except Exception as e:
                        print(f"⚠️ 提取某一天价格失败: {e}")
                        continue

                print("✅ 一周价格提取完成：")
                for wp in week_prices:
                    print(wp)
                
                return economy_prices, week_prices

            except Exception as e:
                print(f"⚠️ 提取一周价格时出错: {e}")
                return economy_prices, []

        return economy_prices, []

    except TimeoutException:
        print("⏱️ 超时：30秒内未加载出有效航班内容，已跳过该项。")
        return [], []
    except Exception as e:
        print(f"❌ 异常发生：{e}")
        return [], []

# ✅ 追加写入 CSV
def append_to_csv(row):
    df = pd.DataFrame([row])
    df.to_csv(csv_file, mode='a', index=False, header=False)
    print(f"💾 已保存结果: {row['departure']} → {row['arrival']}")

# ✅ 主流程
for arrival_code in target_airports:
    driver = init_driver()
    wait = WebDriverWait(driver, 20)

    try:
        print(f"\n🔍 查询 {departure_code} → {arrival_code} - 日期: {departure_date_label}")
        driver.get("https://www.turkishairlines.com/")
        time.sleep(4)

        try:
            cookie_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "I accept all cookies")]')))
            cookie_btn.click()
        except:
            pass

        simulate_user_behavior(driver)
        set_airport_code(driver, wait, "fromPort", departure_code)
        set_airport_code(driver, wait, "toPort", arrival_code)
        simulate_user_behavior(driver)
        select_departure_date(driver, wait, departure_date_label)
        simulate_user_behavior(driver)

        search_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Search flights")]')))
        driver.execute_script("arguments[0].click();", search_btn)

        screenshot_name = os.path.join("screenshots", f"result_{departure_code}_{arrival_code}_{departure_date_label.replace(' ', '')}.png")
        prices_economy, prices_week = wait_and_capture_prices(driver, wait, screenshot_name)

        # ✅ 分析当天经济舱价格
        today_price_values = []
        for p in prices_economy:
            try:
                val = float(p["price"].replace(",", "").replace(" ", ""))
                today_price_values.append(val)
            except:
                continue
        lowest_today = min(today_price_values) if today_price_values else None

        # ✅ 分析一周价格
        week_price_values = []
        for p in prices_week:
            try:
                val = float(p["price"].replace(",", "").replace(" ", ""))
                week_price_values.append(val)
            except:
                continue
        lowest_week = min(week_price_values) if week_price_values else None

        # ✅ 查找 arrival_country 和 arrival_continent
        arrival_info = df_airports[df_airports['airport_code'] == arrival_code]
        if not arrival_info.empty:
            arrival_country = arrival_info.iloc[0]['country']
        else:
            arrival_country = "Unknown"

        arrival_continent = None
        for cont in df_countries.columns:
            if arrival_country in df_countries[cont].dropna().tolist():
                arrival_continent = cont
                break
        if arrival_continent is None:
            arrival_continent = "Unknown"

        # ✅ 构建记录
        row = {
            "departure": departure_code,
            "arrival": arrival_code,
            "arrival_country": arrival_country,
            "arrival_continent": arrival_continent,
            "date": departure_date_label,
            "prices": json.dumps(prices_economy, ensure_ascii=False),
            "lowest_price_today": lowest_today,
            "week_prices": json.dumps(prices_week, ensure_ascii=False),
            "lowest_price_week": lowest_week
        }

        append_to_csv(row)

    except Exception as e:
        print(f"❌ 查询失败 {departure_code} → {arrival_code}：{e}")

    finally:
        driver.quit()
        time.sleep(random.uniform(2.0, 4.0))

print("\n✅ 所有查询完成！")
