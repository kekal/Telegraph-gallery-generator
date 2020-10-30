
# coding=utf-8
import subprocess
import sys
import traceback
import os
import argparse
import time
import logging
import logging.handlers


ACCESS_TOKEN = ""
CHAT_URL = "https://my_page"
RESERVED_FOLDERS = ['temp', '.idea', 'old', '.git', 'Old']
EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif")
HEADER_NAME = "My albums page"
WIDTH = 3000
HEIGHT = 2000
SIZE = 9000000
DOMAIN = "https://telegra.ph"
LOG_FILE_NAME = "log.txt"
RESULTS_FILE_NAME = "results.txt"

# ======================================================================
# ======================================================================

subprocess.check_call([sys.executable, "-m", "pip", "--disable-pip-version-check", "install", "telegraph==1.4.1"])
subprocess.check_call([sys.executable, "-m", "pip", "--disable-pip-version-check", "install", "Pillow==8.0.1"])

from telegraph import Telegraph, upload
from PIL import Image


# ======================================================================
# ======================================================================

class ReadArgs:
    token = ''
    pause = 2
    input_folder = ''
    output_folder = ''
    height = -1
    width = -1
    size = -1


def setup_logger():
    handler_file = logging.handlers.WatchedFileHandler(os.environ.get("LOGFILE", LOG_FILE_NAME))
    std_handler = logging.StreamHandler(sys.stdout)
    formatter_for_file = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
    formatter_for_std = logging.Formatter('%(message)s')
    handler_file.setFormatter(formatter_for_file)
    std_handler.setFormatter(formatter_for_std)
    root = logging.getLogger()
    root.setLevel(os.environ.get("LOGLEVEL", "INFO"))
    root.addHandler(handler_file)
    root.addHandler(std_handler)

    return root

def create_or_attach_to_telegraph_account():
    if should_create_account:
        __telegraph = Telegraph()
        __telegraph.create_account("Anonymous")
    else:
        __telegraph = Telegraph(access_token=read_args.token)

    logger.info("Currently used token: " + str(__telegraph.get_access_token()))
    return __telegraph

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
    global should_create_account
    args = parse_input()

    if not validate_folder(args.input_folder):
        args.input_folder = '.\\'
        args.output_folder = args.input_folder + '.\\old\\'
    else:
        if not validate_folder(args.output_folder):
            args.output_folder = args.input_folder + '\\old\\'

    if args.token is None or args.token == "":
        args.token = ACCESS_TOKEN
        if args.token is None or args.token == "":
            should_create_account = True

    if not validate_pause(args.pause):
        args.pause = 2

    return args


def print_header(__args):
    logger.info('\n========================================================================\n========================================================================\n')
    logger.info('Starting in the directory: "' + os.getcwd() + '"')
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

    return list(filter(lambda f: f.lower().endswith(EXTENSIONS), __files))


def validate_pause(_pause):
    return not (_pause is None or _pause < 0)


def parse_input():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--pause', help='↑ Upload pause in seconds', type=int)
    parser.add_argument('-t', '--token', help='↑ Account token', type=str)
    parser.add_argument('-i', '--input', help='↑ Input folder', type=str, required=True)
    parser.add_argument('-o', '--output', help='↑ Output folder', type=str)
    parser.add_argument('-he', '--height', help='↑ Maximum image height', type=int)
    parser.add_argument('-wi', '--width', help='↑ Maximum image width', type=int)
    parser.add_argument('-s', '--size', help='← Maximum image file size', type=int)


    # parser.print_help()
    args = parser.parse_args()

    __args = ReadArgs()

    __args.token = args.token
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
        __upload_path =  __full_path = __directory + '\\' + __file_name

        logger.info("\nUploading: " + __full_path)

        if (not validate_image_dimensions(__full_path)) or (not validate_file_size(__full_path)):
            __upload_path = run_image_downgrade(__full_path)

        try:
            image_path = upload.upload_file(__upload_path)
        except BaseException as __e:
            body = getattr(__e, 'doc', '')
            logger.error("     File " + str(__file_name) + " will be skipped.\n     Error:   " + str(__e) + '\n     Error body:\n' + str(body) + '\n' + str(traceback.format_exc()))
            __errors.append(str(__file_name) + ' : ' + str(__e))
            continue

        logger.info("Uploaded:  " + DOMAIN + image_path[0])

        move_image_to_output_folder(__full_path, __directory, __file_name)

        image_paths.append(image_path[0])
        time.sleep(__pause)

    remove_uploaded_folder(__directory)

    return image_paths


def validate_image_dimensions(__full_path):
    __im = Image.open(__full_path)
    __width, __height = __im.size

    return __width <= WIDTH and __height <= HEIGHT


def validate_file_size(full_path):
    __file_size = os.stat(full_path).st_size
    return True if __file_size < SIZE else False


def run_image_downgrade(__full_path):
    __need_downscale = not validate_image_dimensions(__full_path)
    __need_downsize = not validate_file_size(__full_path)

    __trimmed_path = str(os.path.splitext(__full_path)[0])
    __im = Image.open(__full_path)

    if __need_downscale:
        __width, __height = __im.size
        __w_percent = (WIDTH / float(__width))
        __h_percent = (HEIGHT / float(__height))
        __percent = min(__w_percent, __h_percent)
        __new_width = int(float(__width) * (float(__percent)))
        __new_height = int(float(__height) * (float(__percent)))

        __im = __im.resize((__new_width, __new_height), Image.ANTIALIAS)

    if __need_downsize:
        __compressed_path = compress_image(__trimmed_path, __im)
        return __compressed_path

    else:
        __im.save(__trimmed_path + "_c.jpg", "JPEG", optimize=True, quality=100)
        return __trimmed_path + "_c.jpg"


def compress_image(__trimmed_path, img):
    __quality = 100
    try:
        os.remove(__trimmed_path + "_c.jpg")
    except IOError as __e:
        pass

    __current_size = SIZE + 1
    while __current_size > SIZE:
        if __quality == 0:
            os.remove(__trimmed_path + "_c.jpg")
            logger.error("Error: File cannot be compressed below " + str(SIZE))
            break

        img.save(__trimmed_path + "_c.jpg", "JPEG", optimize=True, quality=__quality)

        __current_size = os.stat(__trimmed_path + "_c.jpg").st_size
        __quality -= 1

    return __trimmed_path + "_c.jpg"


def remove_uploaded_folder(__directory):
    try:
        if not os.listdir(__directory):
            os.rmdir(__directory)
    except BaseException as __e:
        logger.error("     " + str(__e) + '\n' + str(traceback.format_exc()))


def move_image_to_output_folder(__old_path, __set_name, __file_name):
    try:
        old_folder = read_args.output_folder + '\\' + __set_name
        if not os.path.exists(old_folder):
            os.makedirs(old_folder)

        os.replace(__old_path, old_folder + '\\' + __file_name)
        logger.info(__file_name + ' was moved to the ' + old_folder)

    except BaseException as __e:
        logger.error("     " + str(__e) + '\n' + str(traceback.format_exc()))


def create_page_body(__image_urls):
    body = '<p><a href="' + CHAT_URL + '" target="_blank">'+ HEADER_NAME +'</a></p>'
    for __url in __image_urls:
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

    return post_link, len(image_urls)


def add_page_to_results(__set_name, __url, __count):
    f = open(RESULTS_FILE_NAME, "a")
    f.write(__set_name + ' : ' + str(__count) + ' : ' + __url + '\n')
    f.close()


# ======================================================================
# ========================= Main routine ===============================
# ======================================================================

should_create_account = False

logger = setup_logger()


try:
    read_args = read_validate_input()

    os.chdir(read_args.input_folder)

    print_header(read_args)

    telegraph = create_or_attach_to_telegraph_account()

    dirs_list = get_sub_dirs_list(read_args.input_folder)

    for set_directory in dirs_list:
        try:
            url, __count = elaborate_directory(set_directory)
            add_page_to_results(set_directory, url, __count)

        except BaseException as e:
            logger.fatal(set_directory + ' could not be uploaded.\nError: ' + str(e) + '\n' + str(traceback.format_exc()))

except BaseException as e:
    logger.fatal("Critical error: " + str(e) + '\n' + str(traceback.format_exc()))

sys.exit()


