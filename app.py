from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
import pandas as pd
from time import sleep
from datetime import datetime

ser = Service('./chromedriver')
options = webdriver.ChromeOptions()
options.add_argument("--lang=en-US")
driver = webdriver.Chrome(service=ser, options=options)

url = "https://twitter.com/search?q={}%20since:{}%20until:{}%20{}&src=typed_query&f=live"
account_url = "https://twitter.com/search?q=(from%3A{})%20since:{}%20until:{}%20{}&src=typed_query&f=live"

main_div = "//div[contains(@aria-label, 'Search')]/div/div/div/div/article/div/div/div/div[2]/div[2]/div[2]"


def search(word, count=10, fdate='2022-02-01', tdate="2022-02-12", account_name=None, replies=False):
    max_tries = 10
    remaining_tries = max_tries

    filter = ''
    if(not replies):
        filter += "-filter:replies"

    current_time = str(datetime.now())
    current_time = current_time.replace(':', '_')
    current_time = current_time.replace(' ', '_')
    current_time = current_time.replace('.', '_')
    save_name = word.replace(' ', '').replace('#', '') + current_time + '.csv'

    tweets = []
    imgs = []
    reply_info = []
    if(account_name is None):
        driver.get(url.format(word.replace('#', '%23'), fdate, tdate, filter))
    else:
        driver.get(account_url.format(account_name, fdate, tdate, filter))
    driver.execute_script("document.body.style.zoom = '0.5';")
    sleep(4)

    while(len(set(tweets)) < count):
        if remaining_tries <= 0:
            break
        try:
            _tweets = []
            _imgs = []
            _reply_info = []
            for t in driver.find_elements(By.XPATH, main_div):
                try:
                    is_reply = False
                    tweet_content = t.find_element(By.XPATH, "div[1]")
                    # check if the tweet is a reply
                    if("replying" in tweet_content.text.lower()):
                        is_reply = True

                    tweet_imgs_elements = t.find_elements(
                        By.XPATH, "div[2]//img")

                    if(is_reply):
                        tweet_content = t.find_element(By.XPATH, "div[2]")
                        tweet_imgs_elements = t.find_elements(
                            By.XPATH, "div[3]//img")
                    tweet_imgs = []
                    for img in tweet_imgs_elements:
                        img_url = img.get_attribute('src')
                        if('emoji' not in img_url):
                            tweet_imgs.append(img_url)
                    _tweets.append(tweet_content.text)
                    _imgs.append(tweet_imgs)
                    _reply_info.append(is_reply)
                except StaleElementReferenceException:
                    pass
            if(len(set(tweets)) == len(set(tweets + _tweets))):
                remaining_tries -= 1
                driver.execute_script(
                    "window.scrollTo(0,-document.body.scrollHeight);")
                print('remaining_tries:', remaining_tries)
            tweets.extend(_tweets)
            imgs.extend(_imgs)
            reply_info.extend(_reply_info)
            sleep(2)
            # scroll one page down
            driver.execute_script(
                "window.scrollTo(0,document.body.scrollHeight);")
            # save tweets
            df = pd.DataFrame({'tweet': tweets,
                               'imgs': imgs,
                               'hashtag': [word] * len(tweets),
                               "is_reply": reply_info,
                               'query_account': [account_name] * len(tweets)
                               })
            df = df.drop_duplicates(subset=['tweet'])
            df.to_csv(save_name, index=False, encoding='utf-8-sig')
            print('Saved', len(df), ' Tweets: ', save_name)
        except KeyboardInterrupt:
            break


def search_words(words_to_search):
    for w, d in words_to_search:
        print("Collecting:", w, '...')
        search(w, 10000, d)
        print("#" * 50)


def search_accounts(accounts):
    for acc, d in accounts:
        print("Collecting tweets of : @{}...".format(acc))
        search("", 10000, d, account_name=acc, replies=True)
        print("#" * 50)


words_to_search = [
    (
        "#NFT",
        "2022-01-01",
    ),
]


accounts = [
    (
        'twitter',
        "2022-01-01",
    ),
]

# search_words(words_to_search)
# search_accounts(accounts)
