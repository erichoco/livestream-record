import os
import sys
import select
import signal
import time
import re
import subprocess
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException

import recording.screencast as screencast


# Selenium

def init_driver():
    prefs = {}
    prefs['profile.default_content_setting_values.plugins'] = 1
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_experimental_option('prefs', prefs)
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

def bring_browser_to_front(driver):
    driver.execute_script('alert(1);')
    driver.switch_to_alert().accept()

def teardown(driver):
    driver.quit()


# Crawlers

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
                "time": time.time(),
                "name": name,
                "message": content
            })

    except (NoSuchElementException, StaleElementReferenceException):
        pass
    except:
        print("[Messages] Exception:", sys.exc_info()[0])
        raise

    if new_messages:
        print("==== New Messages ====", new_messages)

    return messages + new_messages

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

            # Update gift count to same gift found
            for g in gifts[-10:]:
                if g["name"] == name and g["gift"] == content and g["count"] <= count:
                    g["count"] = count
                    new_gifts.append(g) # for printing
                    break
            else:
                g = {
                    "time": time.time(),
                    "name": name,
                    "gift": content,
                    "count": count
                }
                gifts.append(g)
                new_gifts.append(g)

    except (NoSuchElementException, StaleElementReferenceException):
        pass
    except:
        print("[Gifts] Exception:", sys.exc_info()[0])
        raise

    if new_gifts:
        print("==== New Gifts ====")
        for g in new_gifts:
            print("name: {} gift: {} count: {}".format(g["name"], g["gift"], g["count"]))

    return gifts

def crawl_star(stars):
    try:
        new_item = driver.find_element_by_css_selector("strong.starNum.star")
        new_item = new_item.text

        if not stars or new_item != stars[-1]["star"]:
            stars.append({
                "time": time.time(),
                "star": new_item
            })

    except (NoSuchElementException, StaleElementReferenceException):
        pass
    except:
        print("[Star] Exception:", sys.exc_info()[0])
        raise

    return stars

def crawl_viewer_num(view_num):
    try:
        new_item = driver.find_element_by_css_selector("p.onWatch")
        new_item = new_item.text[:-2]

        if not view_num or new_item != view_num[-1]["num"]:
            view_num.append({
                "time": time.time(),
                "num": new_item
            })

    except (NoSuchElementException, StaleElementReferenceException):
        pass
    except:
        print("[View Num] Exception:", sys.exc_info()[0])
        raise

    return view_num

def crawl_info(info):
    try:
        info["messages"] = crawl_messages(info["messages"])
        info["gifts"] = crawl_gifts(info["gifts"])
        info["stars"] = crawl_star(info["stars"])
        info["view_nums"] = crawl_viewer_num(info["view_nums"])
    except:
        raise

    return info


# Process CSV

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

def time_elapsed(diff):
    return "{hour:02d}:{min:02d}:{sec:02d}".format(
        hour=int(diff//3600)%3600,
        min=int((diff//60)%60),
        sec=int(diff%60))

def save_info(writer, info, type, start_time):
    for v in info:
        value_1, value_2, value_3 = "", "", ""
        if type == "viewers":
            value_1, value_2, value_3 = "", "", v["num"]
        elif type == "stars":
            value_1, value_2, value_3 = "", "", v["star"]
        elif type == "gift":
            value_1, value_2, value_3 = v["name"], v["gift"], v["count"]
        elif type == "message":
            value_1, value_2, value_3 = v["name"], v["message"], ""

        writer.writerow([
            time.strftime("%m-%d_%H:%M:%S", time.gmtime(v["time"])),
            time_elapsed(v["time"] - start_time),
            type,
            value_1,
            value_2,
            value_3
        ])

def save_info_partial(writer, info, type, start_time):
    cur = time.time()
    idx = 0
    for (i, v) in enumerate(info):
        # print(i, v["time"])
        if time.gmtime(cur - v["time"])[4] < 1:
            idx = i
            break
    save_info(writer, info[:idx], type, start_time)
    return info[idx:]

def save_csv(write, info):
    save_info(writer, info["view_nums"], "viewers", info["start_time"])
    save_info(writer, info["stars"], "stars", info["start_time"])
    save_info(writer, info["gifts"], "gift", info["start_time"])
    save_info(writer, info["messages"], "message", info["start_time"])

def save_csv_partial(writer, info):
    print("saving csv")
    info["view_nums"] = save_info_partial(writer, info["view_nums"], "viewers", info["start_time"])
    info["stars"] = save_info_partial(writer, info["stars"], "stars", info["start_time"])
    info["gifts"] = save_info_partial(writer, info["gifts"], "gift", info["start_time"])
    info["messages"] = save_info_partial(writer, info["messages"], "message", info["start_time"])
    return info


# Main

def check_param(argv):
    if len(argv) < 2:
        print("Please provide livestream id.")
        return False
    try:
        val = int(argv[1])
    except ValueError:
        return False
    return True

if __name__ == "__main__":
    if not check_param(sys.argv):
        exit(0)

    room_url = "https://web.immomo.com/live/" + sys.argv[1] + "?rf=683"
    chat_box_class_name = "live-msg-list"
    driver = init_driver()    
    if not load_chat_box(driver, room_url, chat_box_class_name):
        driver.quit()
        exit(0)
        
    info = init_info(room_url)
    path = init_csv(info)
    start_time = time.time()
    cur_time = time.strftime("_%m-%d_%H-%M-%S", time.gmtime())

    screen = screencast.Screencast(path, cur_time)
    screen.start()
    # audio = subprocess.Popen(['python3', 'recording/audiocast.py', '-p', path, '-s', cur_time])

    with open(path + "/data" + cur_time + ".csv", "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, delimiter=",")
        writer.writerow(["timestamp", "time", "event", "value_1", "value_2", "value_3"])

        try:
            last_crawl = time.gmtime()[5] # get current second
            last_save = time.gmtime()[4]
            while True:
                if (time.gmtime()[5] != last_crawl):
                    info = crawl_info(info)
                    last_crawl = time.gmtime()[5]
                if (time.gmtime()[4] != last_save):
                    info = save_csv_partial(writer, info)
                    last_save = time.gmtime()[4]

                # press 'q' & 'return' to break
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    save_csv(writer, info)
                    raise KeyboardInterrupt

                # break after 2 hrs
                if time.gmtime(time.time() - start_time)[3] > 1:
                    raise KeyboardInterrupt

        except KeyboardInterrupt:
            pass
        except Exception as e:
            print("Unknown Exception")
            print(e)
    
    screen.stop()
    driver.quit()
