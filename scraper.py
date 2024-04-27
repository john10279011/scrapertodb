import json
import re
import requests
from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager

# Initialize WebDriver using GeckoDriverManager
driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())

url = "http://admin:admin@197.155.149.22/default/en_US/tools.html?type=sms_inbox"

driver.get(url)


def scrape():
    data = []

    tb = driver.find_element_by_xpath("//table[contains(@id,'l1_sms_store')]/tbody")
    rows = tb.find_elements_by_xpath(".//tr")

    for index, row in enumerate(rows):
        try:
            sms_content = row.find_element_by_xpath(
                ".//td[contains(@class,'sms_content')]"
            ).text

            amount_match = re.search(r"Montant : (\d+(?:\.\d+)?)", sms_content)
            if amount_match:
                amount_info = amount_match.group(1)

                info_dict = {
                    "sender": "",
                    "from": "",
                    "amount": amount_info,
                    "reference": "",
                    "content": sms_content,
                }

                try:
                    number_match = re.search(r"numero (\d+(?:\.\d+)?)", sms_content)
                    number_info = number_match.group(1)
                    info_dict["sender"] = number_info
                except:
                    pass

                if index > 0:
                    prev_row = rows[index - 1]
                    try:
                        time = prev_row.find_element_by_xpath(
                            ".//td[contains(@class,'row11')][1]"
                        ).text
                        info_dict["reference"] = time[5:]
                    except:
                        info_dict["reference"] = "Time not found"

                    try:
                        pfrom = prev_row.find_element_by_xpath(
                            ".//td[contains(@class,'row11')][2]"
                        ).text
                        info_dict["from"] = pfrom[5:]
                    except:
                        info_dict["from"] = "From not found"
                else:
                    info_dict["reference"] = "No time information found"
                    info_dict["from"] = "No sender information found"

                data.append(info_dict)

        except Exception as e:
            pass

    return data


data1 = scrape()
click = driver.find_element_by_xpath("//input[contains(@value,'2')]").click()
data2 = scrape()

combined_data = data1 + data2

# Sending data through the webhook
webhook_url = "http://104.248.60.135/marchepro/webhook-receiver"

for item in combined_data:
    try:
        response = requests.post(webhook_url, json=item)
        if response.status_code == 200:
            print("Data sent successfully:", item)
        else:
            print("Failed to send data:", item)
            print("Response:", response.status_code, response.text)
    except Exception as e:
        print("Error sending data:", item)
        print("Exception:", str(e))

print("Scraped data:")
for item in combined_data:
    print(json.dumps(item, indent=4))

driver.quit()
