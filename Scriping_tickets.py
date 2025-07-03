import os
import time
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
departure_code = "GVA"
contients = ["Africa", "Asia", "Europe", "North America", "South America", "Oceania"]
selected_continents = [contients[3], contients[4], contients[5]]
file_path = 'Fly_Across_6_Continents.xlsx'
departure_date_label = "Wed Aug 06 2025"

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
csv_file = "turkish_prices_results.csv"
if not os.path.exists(csv_file):
    pd.DataFrame(columns=["departure", "arrival", "date", "prices", "lowest_price"]).to_csv(csv_file, index=False)

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
    input_box = wait.until(EC.element_to_be_clickable((By.ID, input_id)))
    input_box.click()
    time.sleep(0.2)
    input_box.send_keys(Keys.CONTROL + "a")
    input_box.send_keys(Keys.DELETE)
    time.sleep(0.1)
    input_box = wait.until(EC.element_to_be_clickable((By.ID, input_id)))
    input_box.click()
    time.sleep(0.2)
    input_box.send_keys(airport_code)
    time.sleep(1.5)
    suggestion = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'ul[role="listbox"] > li[role="button"]')))
    driver.execute_script("arguments[0].click();", suggestion)

# ✅ 选择日期
def select_departure_date(driver, wait, label_str):
    date_area = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.hm__RoundAndOneWayTab_datePassengerArea__jToT9")))
    driver.execute_script("arguments[0].click();", date_area)
    time.sleep(1.5)
    spans = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'button span[aria-label]')))
    for span in spans:
        if span.get_attribute("aria-label").strip() == label_str:
            button = span.find_element(By.XPATH, "./ancestor::button")
            driver.execute_script("arguments[0].click();", button)
            print(f"✅ 日期选择成功: {label_str}")
            return
    raise Exception(f"❌ 未找到日期: {label_str}")

# ✅ 等待并提取价格
def wait_and_capture_prices(driver, wait, screenshot_name):
    try:
        try:
            WebDriverWait(driver, 6).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[id*="ForceRedirectBaseModal"]'))
            )
            print("⚠️ 当前无可用航班，已跳过截图与解析。")
            return []
        except TimeoutException:
            pass

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class*="av__FlightPanel_flightList__gxfmQ"]'))
        )
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class*="av__FlightItem_flightItem__BGnIP"]'))
        )
        time.sleep(1.2)

        economy_prices = []
        price_blocks = driver.find_elements(By.CSS_SELECTOR, 'div[class*="av__FlightItem_flightItem__BGnIP"]')
        for block in price_blocks:
            try:
                price_info = block.find_element(By.CSS_SELECTOR, 'span[class*="av__style_price-type-content__3xWFY"]').text.strip()
                price_lines = price_info.split("\n")
                price_val = price_lines[0].strip()
                currency = "".join(price_lines[1:]).strip()
                economy_prices.append({
                    "price": price_val,
                    "currency": currency
                })
            except:
                continue

        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)
        driver.save_screenshot(screenshot_name)
        print(f"📸 已截图：{screenshot_name}")
        return economy_prices

    except TimeoutException:
        print("⏱️ 超时：30秒内未加载出有效航班内容，已跳过该项。")
        return []
    except Exception as e:
        print(f"❌ 异常发生：{e}")
        return []

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
        prices = wait_and_capture_prices(driver, wait, screenshot_name)

        # ✅ 分析并保存价格
        price_values = []
        for p in prices:
            try:
                val = float(p["price"].replace(",", "").replace(" ", ""))
                price_values.append(val)
            except:
                continue
        lowest = min(price_values) if price_values else None

        row = {
            "departure": departure_code,
            "arrival": arrival_code,
            "date": departure_date_label,
            "prices": str(prices),
            "lowest_price": lowest
        }
        append_to_csv(row)

    except Exception as e:
        print(f"❌ 查询失败 {departure_code} → {arrival_code}：{e}")

    finally:
        driver.quit()
        time.sleep(random.uniform(2.0, 4.0))

print("\n✅ 所有查询完成！")
