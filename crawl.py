# 运行请前先运行
# mkdir "D:\AutomationProfile\edge"
# .\msedge.exe --remote-debugging-port=9222 --user-data-dir="D:\AutomationProfile\edge"

import json
from selenium import webdriver
from selenium.webdriver.common.by import By
import time


options = webdriver.EdgeOptions()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Edge(options=options)

try:
    topic = "shell"
    # topic = "dockerfile"
    pages = 100
    pagesize = 50
    for page in range(30, pages+1):
        for index in range(1, pagesize+1):
            driver.get(f"https://stackoverflow.com/questions/tagged/{topic}?page={page}&sort=votes&pagesize={pagesize}")
            time.sleep(1)
            question_link = driver.find_element(By.XPATH, f"/html/body/div[8]/div[3]/div[1]/div[3]/div[{index}]/div[2]/h3/a")
            question_url = question_link.get_attribute("href")
            driver.get(question_url)
            time.sleep(1)

            question_title = driver.find_element(By.CSS_SELECTOR, "#question-header > h1 > a").text
            print(f"Question Title: {question_title}")

            try:
                answer = driver.find_element(By.XPATH, "/html/body/div[8]/div[3]/div/div[1]/div[3]/div[3]/div[3]/div/div[2]/div[1]").text
            except Exception as e:
                answer = driver.find_element(By.XPATH, "/html/body/div[8]/div[3]/div/div[1]/div[3]/div[3]/div[2]/div/div[2]/div[1]").text
            print(f"Question Answer: {answer}")

            with open(f"{topic}.json", "r", encoding="utf-8") as result:
                try:
                    data = json.load(result)
                except json.JSONDecodeError:
                    data = {}
                data.update({question_title: answer})
            with open(f"{topic}.json", "w", encoding="utf-8") as result:
                json.dump(data, result, indent=4)
            print("index: ", index)
        print("page: ", page)
finally:
    driver.quit()
