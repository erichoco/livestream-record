import os
import sys
import signal
import time
import re
import subprocess
# import unicodecsv as csv
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException

import recording.screencast as screencast


def init_info(url):
    info = {}
    info["messages"] = []
    info["gifts"] = []
    info["stars"] = []
    info["view_nums"] = []
    info["room_url"] = url
    info["start_time"] = round(time.time())
    room_id = re.search("live/([0-9]+)\?rf", url)
    if room_id:
        info["room_id"] = room_id.group(1)
    else:
        info["room_id"] = ""
    return info

def init_fieldnames():
    return ["timestamp", "time", "viewers", "stars",
        "comment-user", "comment-message",
        "gift-user", "gift-name", "gift-count"]

def init_driver():
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument("--mute-audio")
    # chrome_options.add_argument("--start-maximized")

    driver = webdriver.Chrome('driver/chromedriver', chrome_options=chrome_options)

    # calling driver.wait.until would wait 5s for the element to be loaded before throwing exception
    driver.wait = WebDriverWait(driver, 5)

    return driver

def load_chat_box(driver, url, class_name):
    driver.get(url)
    try:
        box = driver.wait.until(EC.presence_of_element_located((By.CLASS_NAME, class_name)))
        return True

    except TimeoutException:
        print("Live chat box not found.")
        print("Check CSS class name of the chat box.")
        return False

def crawl_messages(messages):
    new_messages = []

    try:
        new_items = driver.find_elements_by_css_selector("li.live-chat-msg")
        for m in reversed(new_items):
            name = m.find_element_by_class_name("name").text
            content = m.find_element_by_class_name("content").text

            if not (name and content):
                continue

            # Find the last same message
            if messages and messages[-1]["name"] == name and messages[-1]["message"] == content:
                break
            new_messages.insert(0, {
                "time": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
                "name": name,
                "message": content})

    except (NoSuchElementException, StaleElementReferenceException):
        # No messages
        pass

    except:
        print("[Messages] Exception:", sys.exc_info()[0])
        raise

    if new_messages:
        print("==== New Messages ====", new_messages)

    return new_messages

def crawl_gifts(gifts):
    new_gifts = []
    try:
        new_items = driver.find_elements_by_css_selector("li.liveGiftEffectItem")
        for it in new_items:
            div = it.find_element_by_css_selector("div.content")
            name = div.find_element_by_class_name("name").text
            content = div.find_element_by_tag_name("span").text
            count = it.find_element_by_class_name("giftCount").text
            if len(count) >= 2:
                count = int(count[1:])
            else:
                continue

            if not (name and content and count > 0):
                continue

            # Check last 3 gifts crawled (will only show <= 3 gifts on webpage)
            # Update gift count to same gift found
            # for g in gifts[-3:]:
            #     if g["name"] + g["gift"] == name + content:
            #         g["count"] = count
            #         break
            # else:

            new_gifts.append({
                "time": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
                "name": name,
                "gift": content,
                "count": count})

    except (NoSuchElementException, StaleElementReferenceException):
        # No gift now
        pass

    except:
        print("[Gifts] Exception:", sys.exc_info()[0])
        raise

    if new_gifts:
        print("==== New Gifts ====")
        print_gifts(new_gifts)

    return new_gifts

def crawl_star(stars):
    new_star = {}
    try:
        new_item = driver.find_element_by_css_selector("strong.starNum.star")
        new_item = (int)(new_item.text)

        if not stars or new_item > stars[-1]["star"]:
            new_star = {
                "time": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
                "star": new_item
            }

    except (NoSuchElementException, StaleElementReferenceException):
        # No gift now
        pass

    except:
        print("[Star] Exception:", sys.exc_info()[0])
        raise

    return new_star

def crawl_viewer_num(view_num):
    new_num = {}
    try:
        new_item = driver.find_element_by_css_selector("p.onWatch")
        new_item = (int)(new_item.text[:-2])

        if not view_num or new_item != view_num[-1]["num"]:
            new_num = {
                "time": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
                "num": new_item
            }

    except (NoSuchElementException, StaleElementReferenceException):
        # No gift now
        pass

    except:
        print("[View Num] Exception:", sys.exc_info()[0])
        raise

    return new_num

def crawl_info(info):
    try:
        new_messages = crawl_messages(info["messages"])
        new_gifts = crawl_gifts(info["gifts"])
        new_star = crawl_star(info["stars"])
        new_view_num = crawl_viewer_num(info["view_nums"])
    except:
        raise

    info["messages"] += new_messages
    info["gifts"] += new_gifts
    if new_star:
        info["stars"].append(new_star)
    if new_view_num:
        info["view_nums"].append(new_view_num)

    new_info = {
        "messages": new_messages,
        "gifts": new_gifts,
        "star": new_star,
        "view_num": new_view_num
    }

    return info, new_info

def print_gifts(gifts):
    for g in gifts:
        print("name: {} gift: {} count: {}".format(g["name"], g["gift"], g["count"]))

def init_csv(info):
    path = "./data/data"
    if len(info["room_id"]) > 0:
        path += "-" + str(info["room_id"])
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    return path

def save_csv(writer, info, new_info):
    timestamp = time.strftime("%m-%d_%H:%M:%S", time.gmtime())
    diff = round(time.time()) - info["start_time"]
    time_elapsed = "{day}d {hour:02d}:{min:02d}:{sec:02d}".format(
        day=int(diff//86400),
        hour=int(diff//3600),
        min=int(diff//60),
        sec=int(diff%60))

    if new_info["view_num"]:
        writer.writerow([timestamp, time_elapsed, "viewers", new_info["view_num"]["num"]])
    if new_info["star"]:
        writer.writerow([timestamp, time_elapsed, "stars", new_info["star"]["star"]])
    if new_info["gifts"]:
        for g in new_info["gifts"]:
            writer.writerow([timestamp, time_elapsed, "gift", g["name"], g["gift"], g["count"]])
    if new_info["messages"]:
        for m in new_info["messages"]:
            writer.writerow([timestamp, time_elapsed, "message", m["name"], m["message"]])

def dump_csv(info):
    # create subfolder
    path = "./data"
    if len(info["room_id"]) > 0:
        path += "-" + str(info["room_id"])
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    cur_time = time.strftime("%m-%d_%H:%M:%S", time.gmtime())
    # save messages
    with open(path + "/messages_" + cur_time + ".csv", "w", newline="", encoding="utf-8") as csvfile: # python 3
    # with open(path + "/messages_" + cur_time + ".csv", "w") as csvfile: # python 2
        fieldnames = ["time", "name", "message"] # should be same as the keys in info["messages"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, restval="")

        writer.writeheader()
        for m in info["messages"]:
            writer.writerow(m)

    # save gifts
    with open(path + "/gifts_" + cur_time + ".csv", "w", newline="", encoding="utf-8") as csvfile: # python 3
    # with open(path + "/gifts_" + cur_time + ".csv", "w") as csvfile: # python 2
        fieldnames = ["time", "name", "gift", "count"] # should be same as the keys in info["messages"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, restval="")

        writer.writeheader()
        for g in info["gifts"]:
            writer.writerow(g)

def bring_browser_to_front(driver):
    driver.execute_script('alert(1);')
    driver.switch_to_alert().accept()

def teardown(driver):
    driver.quit()


if __name__ == "__main__":
    room_url = "https://web.immomo.com/live/366981145?rf=683"
    chat_box_class_name = "live-msg-list"
    # crawl_timeout = 1

    info = init_info(room_url)
    # fieldnames = init_fieldnames()
    path = init_csv(info)
    driver = init_driver()

    cur_time = time.strftime("_%m-%d_%H-%M-%S", time.gmtime())

    # capture screen & audio
    screen = screencast.Screencast(path, cur_time)

    try:
        if not load_chat_box(driver, room_url, chat_box_class_name):
            driver.quit()
            exit(0)

        bring_browser_to_front(driver)

        # capture screen & audio
        screen.start()
        audio = subprocess.Popen(['python3', 'recording/audiocast.py', '-p', path, '-s', cur_time])

        with open(path + "/data" + cur_time + ".csv", "w", newline="", encoding="utf-8") as csvfile: # python 3
        # with open(path + "/data" + cur_time + ".csv", "w") as csvfile: # python 2
            writer = csv.writer(csvfile, delimiter=",")
            writer.writerow(["timestamp", "time", "event", "value_1", "value_2", "value_3"])

            # start crawling chatroom info
            last_sec = time.gmtime()[5]
            while True:
                cur_sec = time.gmtime()[5]
                if cur_sec == last_sec:
                    continue
                last_sec = cur_sec

                info, new_info = crawl_info(info)
                save_csv(writer, info, new_info)

    except KeyboardInterrupt:
        # dump_csv(info)
        screen.stop()
        teardown(driver)

    except Exception as e:
        # dump_csv(info)
        screen.stop()
        teardown(driver)
        print(e)
