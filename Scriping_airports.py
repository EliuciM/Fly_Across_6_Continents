from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import csv

# 设置无头浏览器（可选）
options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

# 打开土耳其航空网站
driver.get("https://www.turkishairlines.com/")
driver.maximize_window()
time.sleep(5)

# 打开国家选择模态框
country_modal_button = driver.find_element(By.CSS_SELECTOR, 'div.hm__CountrySelect__buttonText__kG5Xt')
country_modal_button.click()
time.sleep(3)

# 获取所有国家元素
countries = driver.find_elements(By.CSS_SELECTOR, "li.hm__CountryModal_countryItem__LnGUY")

# 保存机场信息
results = []

# 遍历每一个国家
for idx, country in enumerate(countries):
    try:
        # 滚动到元素并点击
        driver.execute_script("arguments[0].scrollIntoView();", country)
        time.sleep(0.5)
        country.click()
        time.sleep(2)

        # 获取国家名
        country_name = country.text.strip()

        # 获取机场列表（根据 class 获取 <ul> 下所有 <li>）
        airports_ul = driver.find_element(By.CSS_SELECTOR, "div.hm__CountryModal_cityairportList__Qx5_s > ul")
        airports_li = airports_ul.find_elements(By.TAG_NAME, "li")

        for airport in airports_li:
            airport_code = airport.get_attribute("data-value")
            results.append({
                "country": country_name,
                "airport_code": airport_code
            })

    except Exception as e:
        print(f"跳过 {idx} - 错误: {e}")
        continue

# 关闭浏览器
driver.quit()

# 保存为 CSV 文件
with open("turkish_airlines_airports.csv", "w", newline='', encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["country", "airport_code"])
    writer.writeheader()
    writer.writerows(results)

print("✅ 数据已保存为 turkish_airlines_airports.csv")
