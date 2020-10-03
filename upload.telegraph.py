
# coding=utf-8
import subprocess
import sys
import os
import argparse
import time


ACCESS_TOKEN = "93877a969ce6fcccc32278a3eb39471a3cc3af26d0038ffd74916f312a82"
CHAT_URL = "https://t.me/joinchat/AAAAAFWLulM15aRKgbsSnQ"
AUTHOR_NAME = 'Kekal'
RESERVED_FOLDERS = ['temp', '.idea', 'old']
EXTENSIONS = (".jpg", ".jpeg", ".png")
HEADER_NAME = "ᴡᴏʀʟᴅ ᴏғ ᴄᴏsᴘʟᴀʏ"
WIDTH = 3000
HEIGHT = 2000
SIZE = 9000000
DOMAIN = "https://telegra.ph"


# ======================================================================
# ======================================================================

subprocess.check_call([sys.executable, "-m", "pip", "install", "telegraph"])

from telegraph import Telegraph, upload


# ======================================================================
# ======================================================================

class ReadArgs:
    title = ""
    pause = 2
    input_folder = ''
    output_folder = ''
    height = -1
    width = -1
    size = -1


def validate_folder(__dir):
    if __dir is None or __dir == "":
        return False
    else:
        try:
            if not os.path.exists(__dir):
                print('Directory "' + str(__dir) + '" does not exist or not accessible.')
                sys.exit()
        except TypeError:
            print('Directory "' + str(__dir) + '" does not exist or not accessible.')
            sys.exit()
    return True


def read_validate_input() -> ReadArgs:
    args = parse_input()

    if not validate_folder(args.input_folder):
        args.input_folder = '.\\'

    if not validate_folder(args.output_folder):
        args.output_folder = '.\\old\\'

    if not validate_pause(args.pause):
        args.pause = 2

    if not validate_title(args.title):
        args.title = HEADER_NAME

    return args


def print_header(__args):
    print('Starting in the directory: "' + __args.input_folder + '"')
    print('Output directory: "' + __args.output_folder + '"')
    print('Upload pause: ' + str(__args.pause) + ' seconds')
    print("")
    print("Title: " + __args.title)
    print("")


def get_sub_dirs_list(root_folder):
    __directories = []
    wp = os.walk(root_folder)
    for root, dirs, files in wp:

        for __curr_dir in dirs:
            __all = True
            for res in RESERVED_FOLDERS:
                if __curr_dir != res:
                    continue

                __all = False
                break

            if __all:
                __directories.append(__curr_dir)

    return __directories


def validate_title(__title):
    return not (__title is None or __title == "")


def validate_pause(_pause):
    return not (_pause is None or _pause < 0)


def parse_input():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--title', help='↑ Page title', required=True)
    parser.add_argument('-p', '--pause', help='↑ Upload pause in seconds', type=int)
    parser.add_argument('-i', '--input', help='↑ Input folder', type=str, required=True)
    parser.add_argument('-o', '--output', help='↑ Output folder', type=str, required=True)
    parser.add_argument('-he', '--height', help='↑ Maximum image height', type=int)
    parser.add_argument('-wi', '--width', help='↑ Maximum image width', type=int)
    parser.add_argument('-s', '--size', help='↑ Maximum image file size', type=int)


    # parser.print_help()
    args = parser.parse_args(['-t','Vandych_Lux_school', '-i', 'H:\\tempupload.telegraph','-o' ,'H:\\tempupload.telegraph\old', '-p', '-2'])
    # args = parser.parse_args()

    __args = ReadArgs()

    __args.title = args.title
    __args.pause = args.pause
    __args.input_folder = args.input
    __args.output_folder = args.output
    __args.height = args.height
    __args.width = args.width
    __args.size = args.size

    return __args


def get_files_in_folder(__working_directory):
    for __root1, __dirs, __files in os.walk(__working_directory):
        __files = list(filter(lambda f: f.endswith(EXTENSIONS), __files))
        return __files


def upload_images(__file_paths, __directory, __pause):
    image_paths = []
    for file_path in __file_paths:
        print("Uploading: " + __directory + '\\' + file_path)
        image_path = upload.upload_file(__directory + '\\' + file_path)
        print("Uploaded:  " + DOMAIN + image_path[0])
        image_paths.append(image_path[0])
        time.sleep(__pause)

    return image_paths


def create_page_body(__image_urls):
    body = '<p><a href="' + CHAT_URL + '" target="_blank">'+ HEADER_NAME +'</a></p>'
    for __url in __image_urls:
        body += " <img src='{}'/>".format(__url)

    return body


def post(__title, __body):
    response = telegraph.create_page(__title, html_content=__body)

    return '{}/{}'.format(DOMAIN, response['path'])


# ======================================================================
# ======================================================================



print('')
print('Starting')
print('')


read_args = read_validate_input()

print_header(read_args)

print("Searching for images...")

telegraph = Telegraph(access_token=ACCESS_TOKEN)
telegraph.create_account(short_name=AUTHOR_NAME, author_name=AUTHOR_NAME, author_url=CHAT_URL)
print(telegraph.get_access_token())


dirs_list = get_sub_dirs_list(read_args.input_folder)

for dir1 in dirs_list:
    print(dir1)
    file_names = get_files_in_folder(dir1)

    print(file_names)

    continue
    #
    # for file_name in file_names:
    #     print("   " + file_name + " found")
    #
    # print("")
    #
    # image_urls = upload_images(file_names, wd, sleep)
    #
    # content = create_page_body(image_urls)
    #
    # post_link = post(title_str, content)
    #
    # print('')
    # print(post_link)





