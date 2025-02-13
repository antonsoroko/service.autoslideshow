# -*- coding: utf-8 -*-

# Start a slideshow on Kodi startup or manually.
# Restart the slideshow if the content of the directory has been updated.

import xbmc
import xbmcaddon
import sys
import json
from xbmcvfs import listdir
from time import sleep
from os import path


ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo("id")
currently_played_picture = ""

class KodiMonitor(xbmc.Monitor):

    def __init__(self, **kwargs):
        xbmc.Monitor.__init__(self)

    def onNotification(self, sender, method, data):
        global currently_played_picture
        try:
            #log(f"KodiMonitor: sender {sender}; method: {method}; data: {data}", xbmc.LOGDEBUG)
            if method == "Player.OnPlay":
                data = json.loads(data)
                currently_played_picture = data['item']['file']
        except Exception as e:
            log(e)

def log(message, level=xbmc.LOGINFO):
    xbmc.log(f"[{ADDON_ID}] {message}", level)

def list_dir_recursively(directory):
    content = { 'dirs': {}, 'files': [] }
    dirs, files = listdir(directory)
    content['files'] = files
    for dir in dirs:
        content['dirs'][dir] = list_dir_recursively(path.join(directory, dir))
    return content

def main():
    service_mode = False
    if len(sys.argv) > 0:
        # if launched as program addon then argv[0] == 'script name', and it is empty if launched as service
        if sys.argv[0] == '':
            service_mode = True

    autostart = ADDON.getSetting('autostart')
    if service_mode and autostart == "false":
        log('Autostart disabled, exiting')
        exit()

    monitor = KodiMonitor()
    source_path = ADDON.getSetting('source_path')
    interval = int(ADDON.getSetting('check_interval'))

    # Get initial content of directory and start slideshow
    content1 = list_dir_recursively(source_path)
    xbmc.executebuiltin(f"SlideShow({source_path},recursive)")
    log('Slideshow started, monitoring')

    # Wait for slideshow to start
    sleep(5)

    # Monitor during slideshow
    while not monitor.abortRequested():
        # If slideshow is still running, compare directory old and new content
        if xbmc.getCondVisibility('Window.IsActive(slideshow)'):
            content2 = list_dir_recursively(source_path)
            # Restart slideshow if directory content has changed
            if content1 != content2:
                log('Directory content changed, restarting slideshow')
                xbmc.executebuiltin(f"SlideShow({source_path},recursive,beginslide={currently_played_picture})")
                content1 = content2
        # If slideshow is no longer running (user has exited), exit script
        else:
            break

        # Wait for N seconds, break if abort is requested
        if monitor.waitForAbort(interval):
            break

    log('Finished, exiting')
    exit()

if __name__ == "__main__":
    main()

