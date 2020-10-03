
# coding=utf-8
import subprocess
import sys
import os
import argparse
import time


subprocess.check_call([sys.executable, "-m", "pip", "install", "telegraph"])


from telegraph import Telegraph, upload

# ======================================================================
# ======================================================================

CHAT_URL = "https://t.me/joinchat/AAAAAFWLulM15aRKgbssnQ"

# ======================================================================
# ======================================================================


def parse_input():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--title', help='↑ Page title', required=True)
    parser.add_argument('-f', '--folder', help='↑ Images directory')
    parser.add_argument('-p', '--pause', help='↑ Upload pause in seconds', type=int)
    # parser.print_help()

    args = parser.parse_args(['-t','Title'])

    #args = parser.parse_args()

    dire = args.folder
    tit = args.title
    pause = args.pause

    if dire is None or dire == "":
        dire = '.\\'
    else:
        try:
            if not os.path.exists(dire):
                print('Directory "' + str(dire) + '" does not exist or not accessible.')
                sys.exit()
        except TypeError:
            print('Directory "'+ str(dire) + '" does not exist or not accessible.')
            sys.exit()

    if pause is None or pause < 0:
        pause = 2

    if tit is None or tit == "":
        tit = "ᴡᴏʀʟᴅ ᴏғ ᴄᴏsᴘʟᴀʏ"

    return dire, tit, pause

def get_files(working_path):
    wp = os.walk(working_path)
    for root, dirs, files in wp:
        files[:] = [f for f in files if f.endswith(".jpg") or f.endswith(".jpeg") or f.endswith(".png")]
        return files


def upload_images(file_paths, dire, pause):
    image_paths = []
    for file_path in file_paths:
        print("Uploading: " + dire + '\\' + file_path)
        image_path = upload.upload_file(dire + '\\' + file_path)
        print("Uploaded:  https://telegra.ph" + image_path[0])
        image_paths.append(image_path[0])
        time.sleep(pause)

    return image_paths


def create_page_body(urls):
    body = '<p><a href="' + CHAT_URL + '" target="_blank">ᴡᴏʀʟᴅ ᴏғ ᴄᴏsᴘʟᴀʏ</a></p>'
    for i_url in urls:
        body += " <img src='{}'/>".format(i_url)

    return body


def post(title, body):
    response = telegraph.create_page(title, html_content=body)

    return 'https://telegra.ph/{}'.format(response['path'])


# ======================================================================
# ======================================================================

print('')
print('Starting')
print('')


wd, title_str, sleep = parse_input()


telegraph = Telegraph(access_token='93877a969ce6fcccc32278a3eb39471a3cc3af26d0038ffd74916f312a81')

#telegraph.create_account(short_name='Anonymus', author_name='Anonymus')

print('Starting in the directory: "' + wd + '"')
print('Upload pause: ' + str(sleep) + ' seconds')
print("")
print("Title: " + title_str)
print("")
print("Searching for images...")
file_names = get_files(wd)

for file_name in file_names:
    print("   " + file_name + " found")

print("")

image_urls = upload_images(file_names, wd, sleep)

content = create_page_body(image_urls)

post_link = post(title_str, content)

print(post_link)

