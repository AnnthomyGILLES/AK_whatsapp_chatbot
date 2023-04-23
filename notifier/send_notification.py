import os

from twilio.rest import Client

from utils import load_config

load_config()
# Twilio
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_phone_numer = os.getenv("TWILIO_PHONE_NUMBER")

client = Client(account_sid, auth_token)


def send_message(body_mess, phone_number, media_url=None):
    """
    Send a WhatsApp message to the specified phone number using Twilio.

    Args:
        body_mess (str): The content of the message to send.
        phone_number (str): The recipient's phone number.
    """
    response = client.messages.create(
        from_=f"whatsapp:{twilio_phone_numer}",
        body=body_mess,
        to=f"whatsapp:{phone_number}",
        media_url=media_url,
    )
    print(response.sid)


if __name__ == "__main__":
    # users = UserCollection("users")
    # list_of_users = users.list_all_users()
    # for user in list_of_users:
    #     print(user)
    #     if user["phone_number"] == "+33667656197":
    #         send_message("New feature", user["phone_number"])
    from selenium import webdriver
    from selenium.webdriver.common.keys import Keys
    import time

    # Replace the following strings with your own information
    name = "John Smith"  # The name of the contact you want to message
    message = "Hello, this is a test message."  # The message you want to send

    # Open Chrome and go to WhatsApp Web
    driver = webdriver.Chrome("D:\Téléchargements\chromedriver_win32\chromedriver.exe")
    driver.get("https://web.whatsapp.com/")

    # Wait for user to log in to WhatsApp Web
    input(
        "Press Enter after scanning the QR code on your phone and logging in to WhatsApp Web."
    )

    # Search for the contact by name and click on it
    search_box = driver.find_element_by_xpath(
        '//div[@class="_2_1wd copyable-text selectable-text"]'
    )
    search_box.click()
    search_box.send_keys(name)
    search_box.send_keys(Keys.RETURN)

    # Wait for the chat to load
    time.sleep(5)

    # Type the message and send it
    message_box = driver.find_element_by_xpath('//div[@class="_3uMse"]')
    message_box.click()
    message_box.send_keys(message)
    message_box.send_keys(Keys.RETURN)

    # Close the browser window
    driver.quit()
