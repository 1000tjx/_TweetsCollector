from pydoc import describe
from re import A
from textwrap import indent
from tkinter.messagebox import NO
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
from time import sleep
from datetime import datetime
import json
import os
import sys

ser = Service('./chromedriver')
options = webdriver.ChromeOptions()
options.add_argument("--lang=en-US")
driver = webdriver.Chrome(service=ser, options=options)

url = "https://twitter.com/search?q={}%20since:{}%20until:{}%20{}&src=typed_query&f=live"
account_url = "https://twitter.com/search?q=(from%3A{})%20since:{}%20until:{}%20{}&src=typed_query&f=live"

XPATH_DATA = {
    "normal": {
        "tweet_card_xpath": "//div[contains(@aria-label, 'Search')]/div/div/div/div/div/article/div/div/div/div[2]/div[2]",
        "owner_a_xpath": "div/div/div[1]/div/div/div[2]/div/div[1]/a",
        "tweet_link_xpath": "div/div/div[1]/div/div/div[2]/div/div[3]/a",
        "tweet_time_xpath": "div/div/div[1]/div/div/div[2]/div/div[3]/a/time",
    },
    "conv": {
        "tweet_card_xpath": "//div[contains(@aria-label, 'Conversation')]/div/div/div/div/div/article/div/div/div/div[2]/div[2]",
        "owner_a_xpath": "div/div[1]/div/div/div/div[2]/div/div[1]/a",
        "tweet_link_xpath": "div/div[1]/div/div/div/div[2]/div/div[3]/a",
        "tweet_time_xpath": "div/div[1]/div/div/div/div[2]/div/div[3]/a/time",
    },
    "followers_count": [
        '//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div[1]/div/div[2]/div/div/div/div/div[last()]/div[2]/a/span',
        '//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div[1]/div/div[2]/div/div/div/div/div[last() - 1]/div[2]/a/span',
    ],
}

# in conversation element

show_more_btn1_xpath = '//div[contains(@class, "css-18t94o4 css-1dbjc4n r-1niwhzg r-sdzlij r-1phboty r-rs99b7 r-15ysp7h r-4wgw6l r-1ny4l3l r-ymttw5 r-f727ji r-j2kj52 r-o7ynqc r-6416eg r-lrvibr")]'
show_more_btn2_xpath = '//div[contains(@class, "css-18t94o4 css-1dbjc4n r-1777fci r-1pl7oy7 r-1ny4l3l r-o7ynqc r-6416eg r-13qz1uu")]'

# init 3 windows
# 0 -> search
# 1 -> user_info
# 2 -> conversdation

owners_mem = {}
driver.switch_to.new_window()
sleep(1)
driver.switch_to.new_window()
sleep(1)
driver.switch_to.window(driver.window_handles[0])


def search(
        word="", count=10, fdate='2022-02-01', tdate="2016-02-07", account_name=None, replies=False,
        conversation_url=None, return_json=False, save_name="collected.csv"):

    # init xpath data
    try:
        df = pd.read_csv(save_name, encoding="utf-8-sig")
    except:
        df = pd.DataFrame(
            {
                'owner': [],
                'tweet': [],
                'link': [],
                "like_count": [],
                "reply_count": [],
                "retweet_count": [],
                'imgs': [],
                "is_reply": [],
                'created_at': [],
                'query_account': [],
                'hashtag': [],
            }
        )
    xpath_data = XPATH_DATA['normal']
    if (conversation_url is not None):
        xpath_data = XPATH_DATA['conv']

    max_tries = 500
    remaining_tries = max_tries

    filter = ''
    if (not replies):
        filter += "-filter:replies"

    current_time = str(datetime.now())
    current_time = current_time.replace(':', '_')
    current_time = current_time.replace(' ', '_')
    current_time = current_time.replace('.', '_')
    # save_name = word.replace(' ', '').replace('#', '') + current_time + '.csv'

    tweets = df['tweet'].tolist()
    imgs = df['imgs'].tolist()
    owners = df['owner'].tolist()
    owner_followers = []
    created_at = df['created_at'].tolist()
    tweet_links = df['link'].tolist()
    likes = df['like_count'].tolist()
    retweets = df['retweet_count'].tolist()
    replies = df['reply_count'].tolist()
    reply_info = df['is_reply'].tolist()
    hashtag = df['hashtag'].tolist()
    query_account = df['query_account'].tolist()

    main_div = xpath_data['tweet_card_xpath']
    if (account_name is None):
        search_url = url.format(word.replace('#', '%23'), fdate, tdate, filter)
    else:
        search_url = account_url.format(account_name, fdate, tdate, filter)
    if (conversation_url is not None):
        search_url = conversation_url
    print(search_url)
    driver.get(search_url)
    # driver.execute_script("document.body.style.zoom = '0.7';")
    driver.execute_script("window.scrollTo(0, -document.body.scrollHeight);")
    sleep(2)

    while (len(set(tweets)) < count):
        if remaining_tries <= 0:
            break
        try:
            _tweets = []
            _owners = []
            _owner_followers = []
            _created_at = []
            _tweet_links = []
            _likes = []
            _retweets = []
            _replies = []
            _imgs = []
            _reply_info = []
            _hashtag = []
            _query_account = []
            for t in driver.find_elements(By.XPATH, main_div):
                # print(t.get_attribute("innerText"))
                try:
                    # tweet header
                    tweet_header = t.find_element(By.XPATH, "div[1]")
                    # owner of the tweet
                    owner = tweet_header.find_element(By.XPATH, xpath_data["owner_a_xpath"]).get_attribute("href")
                    t_owner = owner.split("/")[-1]
                    try:
                        t_tweet_link = tweet_header.find_element(
                            By.XPATH, xpath_data["tweet_link_xpath"]).get_attribute("href")
                        t_created_at = tweet_header.find_element(
                            By.XPATH, xpath_data["tweet_time_xpath"]).get_attribute("datetime")
                    except NoSuchElementException:
                        continue

                    is_reply = False
                    t = t.find_element(By.XPATH, "div[2]")
                    tweet_content = t.find_element(By.XPATH, "div[1]")
                    # check if the tweet is a reply
                    if ("replying" in tweet_content.text.lower()):
                        is_reply = True

                    tweet_imgs_elements = t.find_elements(
                        By.XPATH, "div[2]//img")

                    if (is_reply):
                        tweet_content = t.find_element(By.XPATH, "div[2]")
                        tweet_imgs_elements = t.find_elements(
                            By.XPATH, "div[3]//img")
                    tweet_imgs = []
                    for img in tweet_imgs_elements:
                        img_url = img.get_attribute('src')
                        if ('emoji' not in img_url):
                            tweet_imgs.append(img_url)
                    statistics = t.find_element(By.XPATH, "div[last()]/div").get_attribute("aria-label").split(',')
                    reply_count, retweet_count, like_count = [0, 0, 0]
                    if (len(statistics) == 3):
                        reply_count, retweet_count, like_count = [int(w.strip().split(' ')[0]) for w in statistics]

                    # # get tweet owner follower
                    # print("OwnerMem:", owners_mem.get(t_owner))
                    # if (owners_mem.get(t_owner, None) is None):
                    #     o_followers = get_user_followers_count(t_owner)
                    #     owners_mem[t_owner] = o_followers
                    #     _owner_followers.append(owners_mem[t_owner])
                    # else:
                    #     _owner_followers.append(owners_mem[t_owner])
                    if (conversation_url):
                        driver.switch_to.window(driver.window_handles[2])
                    # append data
                    _owners.append(t_owner)
                    _tweets.append(tweet_content.text)
                    _tweet_links.append(t_tweet_link)
                    _likes.append(like_count)
                    _replies.append(reply_count)
                    _retweets.append(retweet_count)
                    _created_at.append(t_created_at)
                    _imgs.append(tweet_imgs)
                    _reply_info.append(is_reply)
                    _hashtag.append(word)
                    _query_account.append(account_name)

                except StaleElementReferenceException as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                    pass
            if (len(set(tweets)) == len(set(tweets + _tweets))):
                remaining_tries -= 1
                driver.execute_script("window.scrollTo(0,-document.body.scrollHeight);")
                print('remaining_tries:', remaining_tries)
            owners.extend(_owners)
            # owner_followers.extend(_owner_followers)
            tweets.extend(_tweets)
            tweet_links.extend(_tweet_links)
            likes.extend(_likes)
            replies.extend(_replies)
            retweets.extend(_retweets)
            created_at.extend(_created_at)
            imgs.extend(_imgs)
            reply_info.extend(_reply_info)
            hashtag.extend(_hashtag)
            query_account.extend(_query_account)
            sleep(1)
            # scroll one page down
            driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")
            # if the page is a conversation / hit show more replies button
            if (conversation_url is not None):
                try:
                    btn = driver.find_element(By.XPATH, show_more_btn1_xpath)
                    btn.click()
                except NoSuchElementException:
                    try:
                        btn = driver.find_element(By.XPATH, show_more_btn2_xpath)
                        btn.click()
                    except:
                        print("Couldn't load more replies!")
                        if (remaining_tries > 1):
                            remaining_tries = 1
                        else:
                            remaining_tries = 0

            # save tweets
            df_dict = {
                'owner': owners,
                # 'owner_followers': owner_followers,
                'tweet': tweets,
                'link': tweet_links,
                "like_count": likes,
                "reply_count": replies,
                "retweet_count": retweets,
                'imgs': imgs,
                "is_reply": reply_info,
                'created_at': created_at,
                'query_account': query_account,
                'hashtag': hashtag,
            }
            # for k, v in df_dict.items():
            #     print(k, len(v))
            df = pd.DataFrame(df_dict)
            df = df.drop_duplicates(subset=['tweet'])
            if (not return_json):
                df.to_csv(save_name, index=False, encoding='utf-8-sig')
                print('Saved', len(df), ' Tweets: ', save_name)
        except KeyboardInterrupt:
            break
    if (return_json):
        return json.loads(df.to_json(orient="records"))


def get_conversation(conversation_link, max_count):
    print("Getting conversation of: " + conversation_link)
    # switch to conversation tab
    driver.switch_to.window(driver.window_handles[2])

    replies = search(conversation_url=conversation_link, count=max_count, return_json=True)
    # for r in replies:
    #     r['owner_followers'] = get_user_followers_count(r["owner"])

    # switchback to search tab
    driver.switch_to.window(driver.window_handles[0])
    return replies


def get_user_followers_count(username):
    print("Getting folowers of: @" + username)
    # switch to user info tab
    driver.switch_to.window(driver.window_handles[1])
    # get data
    driver.get("https://twitter.com/" + username + "/with_replies")
    sleep(2)
    followers = 0
    for xp in XPATH_DATA["followers_count"]:
        try:
            followers = driver.find_element(By.XPATH, xp).get_attribute("innerText")
            break
        except NoSuchElementException:
            print("Couldn't find followers")
            continue
    # switchback to search tab
    sleep(1)
    driver.switch_to.window(driver.window_handles[0])
    return followers


def search_words(words_to_search, save_name="collected.csv"):
    for w, d in words_to_search:
        print("Collecting:", w, '...')
        search(w, 10000, d, save_name=save_name)
        print("#" * 50)


def search_accounts(accounts, save_name="collected.csv"):
    for acc, d, count in accounts:
        print("Collecting tweets of : @{}...".format(acc))
        search("", count, d, account_name=acc, replies=True, save_name=save_name)
        print("#" * 50)


words_to_search = [
    (
        "#NFT",
        "2015-01-01",
    ),
]


accounts = [
    (
        'Twitter',
        "2015-01-01",
        35000,
    ),
]

# search_words(words_to_search)
search_accounts(accounts, save_name="collected.csv")


# Collect replies
# df = pd.read_csv("collected.csv", encoding="utf-8-sig")
# print("!!COLLECTING REPLIES!!")
# replies_col = []
# for i, row in df.iterrows():
#     t_replies_list = get_conversation(row['link'], 10)
#     replies_col.append(json.dumps(t_replies_list))
# df['tweet_replies'] = replies_col
# df.to_csv("collected_with_replies.csv", index=False, encoding="utf-8-sig")


driver.quit()
