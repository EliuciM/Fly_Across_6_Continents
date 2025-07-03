import time
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ========== Step 1: 初始化 WebDriver ==========
options = Options()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=options)
driver.get("https://www.turkishairlines.com/")

wait = WebDriverWait(driver, 20)

# 接受 cookie 弹窗
try:
    cookie_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "I accept all cookies")]'))
    )
    cookie_button.click()
except:
    print("未检测到 Cookie 弹窗或已跳过")

# 等待页面加载完毕
wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

# ========== Step 2: 打开国家模态框 ==========
try:
    modal_opener = wait.until(
        EC.element_to_be_clickable((By.XPATH, '//li[@role="button" and contains(@aria-label, "See all destinations")]'))
    )
    driver.execute_script("arguments[0].click();", modal_opener)  # 更稳定的点击方式

except:
    print("无法打开国家选择框。")
    driver.quit()
    exit()

time.sleep(3)

# ========== Step 3: 获取国家列表 ==========
country_elements = driver.find_elements(By.CSS_SELECTOR, "li.hm__CountryModal_countryItem__LnGuY")

# ========== Step 4: 遍历每个国家并爬机场 ==========
results = []

for idx, country in enumerate(country_elements):
    try:
        # 重新定位国家列表（每次点击模态框内容会被重绘）
        countries = driver.find_elements(By.CSS_SELECTOR, "li.hm__CountryModal_countryItem__LnGuY")
        country_el = countries[idx]
        country_name = country_el.text.strip()

        # 滚动并点击
        driver.execute_script("arguments[0].scrollIntoView();", country_el)
        time.sleep(0.3)
        country_el.click()

        # 等待机场列表更新
        time.sleep(1.5)
        airport_list = driver.find_elements(By.CSS_SELECTOR, "div.hm__CountryModal_cityairportList__QxS_s ul > li")

        for airport in airport_list:
            airport_code = airport.get_attribute("data-value")
            airport_name = airport.text.strip()
            if airport_code:
                results.append({
                    "country": country_name,
                    "airport": airport_name,
                    "airport_code": airport_code
                })

        print(f"✅ 已完成: {country_name}（{len(airport_list)} 个机场）")

    except Exception as e:
        print(f"❌ 跳过第 {idx+1} 个国家，原因: {e}")
        continue

# ========== Step 5: 保存为 CSV ==========
with open("turkish_airports.csv", "w", newline='', encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["country","airport", "airport_code"])
    writer.writeheader()
    writer.writerows(results)

print("✅ 爬取完成，数据已保存为 turkish_airports.csv")

driver.quit()
