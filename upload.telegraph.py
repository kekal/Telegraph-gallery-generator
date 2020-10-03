
# coding=utf-8
import subprocess
import sys
import os
import argparse
import time
import logging
import logging.handlers


ACCESS_TOKEN = "93877a969ce6fcccc32278a3eb39471a3cc3af26d0038ffd74916f312a81"
CHAT_URL = "https://t.me/joinchat/AAAAAFWLulM15aRKgbsSnQ"
RESERVED_FOLDERS = ['temp', '.idea', 'old', '.git']
EXTENSIONS = (".jpg", ".jpeg", ".png")
HEADER_NAME = "ᴡᴏʀʟᴅ ᴏғ ᴄᴏsᴘʟᴀʏ"
WIDTH = 3000
HEIGHT = 2000
SIZE = 9000000
DOMAIN = "https://telegra.ph"
LOG_FILE_NAME = "log.txt"
RESULTS_FILE_NAME = "results.txt"


# ======================================================================
# ======================================================================

subprocess.check_call([sys.executable, "-m", "pip", "install", "telegraph"])

from telegraph import Telegraph, upload


# ======================================================================
# ======================================================================

class ReadArgs:
    pause = 2
    input_folder = ''
    output_folder = ''
    height = -1
    width = -1
    size = -1


def setup_logger():
    handler_file = logging.handlers.WatchedFileHandler(os.environ.get("LOGFILE", LOG_FILE_NAME))
    std_handler = logging.StreamHandler()
    formatter_for_file = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
    formatter_for_std = logging.Formatter('%(message)s')
    handler_file.setFormatter(formatter_for_file)
    std_handler.setFormatter(formatter_for_std)
    root = logging.getLogger()
    root.setLevel(os.environ.get("LOGLEVEL", "INFO"))
    root.addHandler(handler_file)
    root.addHandler(std_handler)

    return root


def validate_folder(__dir):
    if __dir is None or __dir == "":
        return False
    else:
        try:
            if not os.path.exists(__dir):
                logger.fatal('Directory "' + str(__dir) + '" does not exist or not accessible.')
                sys.exit()
        except TypeError:
            logger.fatal('Directory "' + str(__dir) + '" does not exist or not accessible.')
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

    # if not validate_title(args.title):
    #     args.title = HEADER_NAME

    return args


def print_header(__args):
    logger.info('\n========================================================================\n========================================================================\n')
    logger.info('Starting in the directory: "' + __args.input_folder + '"')
    logger.info('Output directory:          "' + __args.output_folder + '"')
    logger.info('Upload pause:              ' + str(__args.pause) + ' seconds')

    if __args.height is not None:
        logger.info('Maximum image height:      ' + str(__args.height) + ' px')
    if __args.width is not None:
        logger.info('Maximum image width:       ' + str(__args.width) + ' px')

    logger.info("")


def get_sub_dirs_list(root_folder):
    dirs= [name for name in os.listdir(root_folder) if os.path.isdir(os.path.join(root_folder, name))]

    return list(filter(lambda d: d not in RESERVED_FOLDERS, dirs))


def get_files_in_folder(__working_directory):
    __files = [name for name in os.listdir(__working_directory) if os.path.isfile(os.path.join(__working_directory, name))]

    #for __root1, __dirs, __files in os.walk(__working_directory):
    return list(filter(lambda f: f.endswith(EXTENSIONS), __files))


# def validate_title(__title):
#     return not (__title is None or __title == "")


def validate_pause(_pause):
    return not (_pause is None or _pause < 0)


def parse_input():
    parser = argparse.ArgumentParser()
    # parser.add_argument('-t', '--title', help='↑ Page title', required=True)
    parser.add_argument('-p', '--pause', help='↑ Upload pause in seconds', type=int)
    parser.add_argument('-i', '--input', help='↑ Input folder', type=str, required=True)
    parser.add_argument('-o', '--output', help='↑ Output folder', type=str, required=True)
    parser.add_argument('-he', '--height', help='↑ Maximum image height', type=int)
    parser.add_argument('-wi', '--width', help='↑ Maximum image width', type=int)
    parser.add_argument('-s', '--size', help='↑ Maximum image file size', type=int)


    # parser.print_help()
    args = parser.parse_args()

    __args = ReadArgs()

    # __args.title = args.title
    __args.pause = args.pause
    __args.input_folder = args.input
    __args.output_folder = args.output
    __args.height = args.height
    __args.width = args.width
    __args.size = args.size

    return __args


def upload_images(__file_names, __directory, __pause, __errors):
    image_paths = []
    for __file_name in __file_names:
        full_path = __directory + '\\' + __file_name
        logger.info("\nUploading: " + full_path)
        try:
            image_path = upload.upload_file(full_path)
        except BaseException as e:
            logger.error("     File " + str(__file_name) + " will be skipped.\n     Error:   " + str(e))
            __errors.append(str(__file_name) + ' : ' + str(e))
            continue

        logger.info("Uploaded:  " + DOMAIN + image_path[0])

        move_image_to_output_folder(full_path, __directory, __file_name)

        image_paths.append(image_path[0])
        time.sleep(__pause)

    remove_uploaded_folder(__directory)

    return image_paths


def remove_uploaded_folder(__directory):
    try:
        if not os.listdir(__directory):
            os.rmdir(__directory)
    except BaseException as e:
        logger.error("     " + str(e))


def move_image_to_output_folder(__old_path, __set_name, __file_name):
    try:
        old_folder = read_args.output_folder + '\\' + __set_name
        if not os.path.exists(old_folder):
            os.makedirs(old_folder)

        os.replace(__old_path, old_folder + '\\' + __file_name)
        logger.info(__file_name + ' was moved to the ' + old_folder)

    except BaseException as e:
        logger.error("     " + str(e))


def create_page_body(__image_urls):
    body = '<p><a href="' + CHAT_URL + '" target="_blank">'+ HEADER_NAME +'</a></p>'
    for __url in __image_urls:
        body += "<br/>"
        body += " <img src='{}'/>".format(__url)

    return body


def post(__title, __body):
    response = telegraph.create_page(__title, html_content=__body)

    return '{}/{}'.format(DOMAIN, response['path'])


def print_errors(__errors):
    if len(__errors) > 0:
        logger.info("\nErrors list:")
        for err in __errors:
            logger.info("   " + err)


def analyze_folder_content(__directory):
    logger.info("Searching for images...")
    __file_names = get_files_in_folder(__directory)
    for file_name in __file_names:
        logger.info("   " + file_name + " found")

    logger.info('\n   ' + str(len(__file_names)) + " files found.\n")

    return __file_names


def elaborate_directory(__set_directory):
    logger.info("\nWorking in directory " + __set_directory + "...\n")
    errors_list = []

    file_names = analyze_folder_content(__set_directory)

    image_urls = upload_images(file_names, __set_directory, read_args.pause, errors_list)

    print_errors(errors_list)

    content = create_page_body(image_urls)
    post_link = post(__set_directory, content)
    logger.info('\n' + post_link + '\n\n')

    return post_link


def add_page_to_results(__set_name, __url):
    f = open(RESULTS_FILE_NAME, "a")
    f.write(__set_name + ' : ' + __url + '\n')
    f.close()


# ======================================================================
# ========================= Main routine ===============================
# ======================================================================

logger = setup_logger()

read_args = read_validate_input()

print_header(read_args)


telegraph = Telegraph(access_token=ACCESS_TOKEN)
#telegraph.create_account(short_name=AUTHOR_NAME, author_name=AUTHOR_NAME, author_url=CHAT_URL)
logger.info("Currently used token: " + telegraph.get_access_token())


dirs_list = get_sub_dirs_list(read_args.input_folder)


for set_directory in dirs_list:
    url = elaborate_directory(set_directory)
    add_page_to_results(set_directory, url)


sys.exit()


