import socket
import socks
import requests
from urllib import parse
import threading
import pickle
import os
import sys
import re
import hashlib
import collections
from pprint import pprint

CACHE_PATH = os.path.join("E:/Cache", 'DKonachan')
POST_SAVE_PATH = os.path.join(CACHE_PATH, 'Pictures')
POST_BACKUP_PATH = os.path.join(POST_SAVE_PATH, 'Backup')
SETTING_FILE_PATH = os.path.join(CACHE_PATH, 'setting.db')
COOKIES_FILE_PATH = os.path.join(CACHE_PATH, 'cookies')
SETTING = {}
SESSION = None
SITEURL = 'https://konachan.net/post'
MAX_POST_DOWNLOAD = 80

SUCCESSED = []
FAILED = []

#socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 13658)
#socket.socket = socks.socksocket


def checkstorage():
    try:
        os.makedirs(CACHE_PATH, exist_ok=True)
        os.makedirs(POST_SAVE_PATH, exist_ok=True)
        os.makedirs(POST_BACKUP_PATH, exist_ok=True)
    except OSError:
        return False
    return True


def loadsetting():
    if os.path.isfile(SETTING_FILE_PATH):
        with open(SETTING_FILE_PATH, 'rb') as f:
            global SETTING
            SETTING = pickle.load(f)
    global SESSION
    SESSION = requests.Session()
    if os.path.isfile(COOKIES_FILE_PATH):
        with open(COOKIES_FILE_PATH, 'rb') as f:
            SESSION.cookies = pickle.load(f)


def savesetting():
    with open(SETTING_FILE_PATH, 'wb') as f:
        pickle.dump(SETTING, f)
    if SESSION and SESSION.cookies is not None:
        with open(COOKIES_FILE_PATH, 'wb') as f:
            pickle.dump(SESSION.cookies, f)


def getlatestpostid():
    response = SESSION.get(SITEURL)
    match = re.search('href="/post/show/([0-9]+)', response.text)
    if match:
        return int(match.group(1))
    else:
        return 0


def correcturl(url):
    if url[0] != 'h':
        url = 'https:' + url
    return url


def downloadpost(postid, saveid):
    url = str.format('https://konachan.net/post/show/{0}', postid)
    response = SESSION.get(url)
    match = re.search('href="(.+)" id="highres-show">', response.text)
    if not match:
        FAILED.append(saveid)
        return
    picpath = correcturl(match.group(1))
    print(str.format('Start downloading: {0}', picpath))
    filename, ext = os.path.splitext(os.path.basename(parse.unquote(picpath)))
    savefilenamebackup = str(postid) + '-' + hashlib.sha256(str.encode(filename)).hexdigest() + ext
    savepathbackup = os.path.join(POST_BACKUP_PATH, savefilenamebackup)
    savepath = os.path.join(POST_SAVE_PATH, savefilenamebackup)
    if os.path.isfile(savepathbackup):
        # with open(savepathbackup, 'rb') as f:
        #     with open(savepath, 'wb') as f2:
        #         f2.write(f.read())
        os.rename(savefilenamebackup, savepath)
        SUCCESSED.append(saveid)
    else:
        response = SESSION.get(picpath)
        if response.status_code == 200:

            with open(savepath, 'wb') as f:
                f.write(response.content)
            # with open(savepathbackup, 'wb') as f:
            #     f.write(response.content)
            SUCCESSED.append(saveid)
        else:
            FAILED.append(saveid)


def main():
    global MAX_POST_DOWNLOAD
    if not checkstorage():
        sys.exit("Can't create cache path: " + CACHE_PATH)
    loadsetting()

    latestid = getlatestpostid()
    if latestid == 0:
        sys.exit("Get latest post id failed, maybe network down....")

    threads = []
    print(str.format('Downloading latest {0} posts......', MAX_POST_DOWNLOAD))

    def dodownloadpost(saveidlist=None):
        for i in range(0, MAX_POST_DOWNLOAD):
            trd = threading.Thread(target=downloadpost,
                                   args=(latestid - i, saveidlist and saveidlist[i] or i),
                                   daemon=False)
            trd.start()
            threads.append(trd)

        for trd in threads:
            trd.join()

    dodownloadpost(FAILED)
    while True:
        if FAILED:
            latestid -= MAX_POST_DOWNLOAD
            MAX_POST_DOWNLOAD = len(FAILED)
            saveidlist = list(FAILED)
            del FAILED[:]
            dodownloadpost(saveidlist)
        else:
            break

    print(str.format("Successed({}):", len(SUCCESSED)))
    pprint(sorted(SUCCESSED))
    print(str.format("Failed({}):", len(FAILED)))
    pprint(sorted(FAILED))

    savesetting()


if __name__ == '__main__':
    main()
