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
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--mute-audio')
    driver = webdriver.Chrome('driver/chromedriver',
        chrome_options=chrome_options)
    # calling driver.wait.until would wait 5s for the element to be loaded before throwing exception
    driver.wait = WebDriverWait(driver, 5)
    return driver

def load_chat_box(driver, url, class_name):
    driver.get(url)
    try:
        box = driver.wait.until(EC.presence_of_element_located((By.CLASS_NAME, class_name)))
        return True

    except TimeoutException:
        print('Live chat box not found.')
        print('Check CSS class name of the chat box.')
        return False

def bring_browser_to_front(driver):
    driver.execute_script('alert(1);')
    driver.switch_to_alert().accept()


# Crawlers

def init_info(url):
    info = {}
    info['messages'] = []
    info['gifts'] = []
    info['view_nums'] = []
    info['room_url'] = url
    info['start_time'] = round(time.time())
    info['room_id'] = re.search('uid=(\d+)', url).group(1)
    return info

def crawl_messages(messages, driver):
    new_messages = []
    try:
        comments_list = driver.find_element_by_css_selector('div.comments_list')
        new_items = reversed(comments_list.find_elements_by_tag_name('li'))

        for m in new_items:
            message = ''
            try:
                message = m.find_element_by_class_name('comments_text').text
            except NoSuchElementException:
                continue
            level = m.find_element_by_tag_name('img').get_attribute('alt')[1:-1]
            name = m.find_element_by_tag_name('span').text[:-1]

            if messages \
                and messages[-1]['name'] == name \
                and messages[-1]['message'] == message:
                break

            new_messages.insert(0, {
                'time': time.time(),
                'name': name,
                'level': level,
                'message': message,
            })

    except (NoSuchElementException, StaleElementReferenceException):
        pass
    except:
        print('[Messages] Exception:', sys.exc_info()[0])
        raise

    if new_messages:
        print('==== New Messages ====', new_messages)

    return messages + new_messages


def crawl_gifts(gifts, driver):
    try:
        new_list = driver.find_element_by_id("js-gift-show-container")
        new_items = new_list.find_elements_by_tag_name("li");

        name, content, count = "", "", 0
        for it in new_items:
            if it.get_attribute("data-playing") == "false":
                continue
            name = it.find_element_by_class_name("name").text
            content = it.find_element_by_class_name("giftType").text[3:]
            count = int(it.find_element_by_class_name("star").get_attribute("data-num"))
            if not (name and content and count > 0):
                continue

            # Update gift count to same gift found
            for g in gifts[-10:]:
                if g["name"] == name and g["gift"] == content and g["count"] <= count:
                    g["count"] = count
                    print("==== Update Gift ====")
                    print("name: {} gift: {} count: {}".format(g["name"], g["gift"], g["count"]))
                    break
            else:
                g = {
                    "time": time.time(),
                    "name": name,
                    "gift": content,
                    "count": count
                }
                gifts.append(g)
                print("==== New Gifts ====")
                print("name: {} gift: {} count: {}".format(g["name"], g["gift"], g["count"]))

    except (NoSuchElementException, StaleElementReferenceException):
        pass
    except:
        print('[Gifts] Exception:', sys.exc_info()[0])
        raise

    return gifts

def crawl_viewer_num(view_num, driver):
    try:
        new_item = driver.find_element_by_css_selector('ul.live_info')
        new_viewer_num = new_item.find_element_by_css_selector('li > span').text

        if not view_num or new_viewer_num != view_num[-1]['num']:
            view_num.append({
                'time': time.time(),
                'num': new_viewer_num,
            })
            print('==== New Viewer Num ====')
            print('num: {}'.format(new_viewer_num))

    except (NoSuchElementException, StaleElementReferenceException):
        pass
    except:
        print('[View Num] Exception:', sys.exc_info()[0])
        raise

    return view_num

def crawl_info(info, driver):
    try:
        info['messages'] = crawl_messages(info['messages'], driver)
        info['gifts'] = crawl_gifts(info['gifts'], driver)
        info['view_nums'] = crawl_viewer_num(info['view_nums'], driver)
    except:
        raise
    return info


# Process CSV

def init_csv(info):
    path = './data/inke/data'
    if len(info['room_id']) > 0:
        path += '-' + str(info['room_id'])
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    return path

def time_elapsed(diff):
    return '{hour:02d}:{min:02d}:{sec:02d}'.format(
        hour=int(diff//3600)%3600,
        min=int((diff//60)%60),
        sec=int(diff%60))

def save_info(writer, info, type, start_time):
    for v in info:
        value_1, value_2, value_3 = '', '', ''
        if type == 'viewers':
            value_1, value_2, value_3 = '', '', v['num']
        elif type == 'gift':
            value_1, value_2, value_3 = v['name'], v['gift'], v['count']
        elif type == 'message':
            value_1, value_2, value_3 = v['name'], v['message'], ''

        writer.writerow([
            time.strftime('%m-%d_%H:%M:%S', time.gmtime(v['time'])),
            time_elapsed(v['time'] - start_time),
            type,
            value_1,
            value_2,
            value_3
        ])

def save_info_partial(writer, info, type, start_time):
    cur = time.time()
    idx = 0
    for (i, v) in enumerate(info):
        # print(i, v['time'])
        if time.gmtime(cur - v['time'])[4] < 1:
            idx = i
            break
    save_info(writer, info[:idx], type, start_time)
    return info[idx:]

def save_csv(write, info):
    save_info(writer, info['view_nums'], 'viewers', info['start_time'])
    save_info(writer, info['gifts'], 'gift', info['start_time'])
    save_info(writer, info['messages'], 'message', info['start_time'])

def save_csv_partial(writer, info):
    print('saving csv')
    info['view_nums'] = save_info_partial(writer, info['view_nums'], 'viewers', info['start_time'])
    info['gifts'] = save_info_partial(writer, info['gifts'], 'gift', info['start_time'])
    info['messages'] = save_info_partial(writer, info['messages'], 'message', info['start_time'])
    return info


# Main

def check_param(argv):
    if len(argv) < 2:
        print('Please provide livestream url.')
        return False
    return True

if __name__ == '__main__':
    if not check_param(sys.argv):
        exit(0)

    room_url = sys.argv[1]
    chat_box_class_name = 'comments_list'
    driver = init_driver()
    if not load_chat_box(driver, room_url, chat_box_class_name):
        driver.quit()
        exit(0)

    info = init_info(room_url)
    path = init_csv(info)
    start_time = time.time()
    start_time_str = time.strftime('_%m-%d_%H-%M-%S', time.gmtime())

    bring_browser_to_front(driver)

    # capture screen & audio
    screen = screencast.Screencast(path, start_time_str)
    screen.start()
    audio = subprocess.Popen(['python3', 'recording/audiocast.py', '-p', path, '-s', start_time_str])

    with open(path + '/data' + start_time_str + '.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(['timestamp', 'time', 'event', 'value_1', 'value_2', 'value_3'])

        try:
            last_crawl = time.gmtime()[5] # get current second
            last_save = time.gmtime()[4]
            while True:
                if (time.gmtime()[5] != last_crawl):
                    info = crawl_info(info, driver)
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
                    save_csv(writer, info)
                    raise KeyboardInterrupt

        except KeyboardInterrupt:
            pass
        except Exception as e:
            print('Unknown Exception')
            print(e)

    screen.stop()
    driver.quit()
