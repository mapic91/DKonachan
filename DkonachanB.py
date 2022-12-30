from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from urllib import parse
import os
import sys
import re
import hashlib
import base64

CACHE_PATH = os.path.join("E:/Cache", 'DKonachan')
POST_SAVE_PATH = os.path.join(CACHE_PATH, 'Pictures')
MAX_POST_DOWNLOAD = 80

imgPath = ["xpath","html/body/div/div/div/div/img"]
imgPathLarge = ["xpath","html/body/img"]
options = webdriver.ChromeOptions()
options.add_argument("--proxy-server=socks5://127.0.0.1:13658")
options.add_argument("--login-profile=zhjx")
driver = webdriver.Chrome(chrome_options=options)
try:
    driver.get("https://konachan.net/post")
    WebDriverWait(driver, 10).until(EC.title_contains("konachan"))
    match = re.search('href="/post/show/([0-9]+)', driver.page_source)
    if match:
        postid = int(match.group(1))
        i = -1
        j = 0
        while j < MAX_POST_DOWNLOAD:
            i = i + 1
            url = str.format('https://konachan.net/post/show/{0}', postid - i)
            driver.get(url)
            base64string = ""
            picpath = ""
            if driver.page_source.find("I'm a teapot") != -1 or \
                    driver.page_source.find("This post does not exist") != -1 or \
                    driver.page_source.find("This post was deleted") != -1:
                continue
            try:
                large = driver.find_element(By.CLASS_NAME, "highres-show")
                picpath = large.get_attribute("href")
                driver.get(picpath)
                try:
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located(imgPathLarge))
                    WebDriverWait(driver, 10).until(EC.visibility_of(driver.find_element(*imgPathLarge)))
                except:
                    continue
                base64string = driver.execute_script('''
                    var c = document.createElement('canvas');
                    var ctx = c.getContext('2d');
                    var img = document.getElementsByTagName("img")[0];
                    c.height=img.naturalHeight;
                    c.width=img.naturalWidth;
                    ctx.drawImage(img, 0, 0,img.naturalWidth, img.naturalHeight);
                    var base64String = c.toDataURL();
                    return base64String;
                ''')
            except NoSuchElementException:
                try:
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located(imgPath))
                    WebDriverWait(driver, 10).until(EC.visibility_of(driver.find_element(*imgPath)))
                except:
                    continue
                picpath = driver.find_element(*imgPath).get_attribute("src")
                base64string = driver.execute_script('''
                    var c = document.createElement('canvas');
                    var ctx = c.getContext('2d');
                    var img = document._getElementsByXPath("html/body/div/div/div/div/img")[0];
                    c.height=img.naturalHeight;
                    c.width=img.naturalWidth;
                    ctx.drawImage(img, 0, 0,img.naturalWidth, img.naturalHeight);
                    var base64String = c.toDataURL();
                    return base64String;
                ''')
            b = base64.b64decode(base64string[22:])
            print(str.format('Start downloading: {0}', picpath))
            filename, ext = os.path.splitext(os.path.basename(parse.unquote(picpath)))
            savefilenamebackup = str(postid) + '-' + hashlib.sha256(str.encode(filename)).hexdigest() + ext
            savepath = os.path.join(POST_SAVE_PATH, savefilenamebackup)
            with open(savepath, 'wb') as f:
                f.write(b)
            j = j + 1
        print("Completed!")
    else:
        sys.exit("Get latest post id failed, maybe network down....")
finally:
    driver.close()