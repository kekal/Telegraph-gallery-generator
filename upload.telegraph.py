
# coding=utf-8

import subprocess
import sys

# ======================================================================
# ======================================================================


subprocess.check_call([sys.executable, "-m", "pip", "--disable-pip-version-check", "install", "Pillow"])
subprocess.check_call([sys.executable, "-m", "pip", "--disable-pip-version-check", "install", "validators"])
subprocess.check_call([sys.executable, "-m", "pip", "--disable-pip-version-check", "install", "requests"])
subprocess.check_call([sys.executable, "-m", "pip", "--disable-pip-version-check", "install", "selenium", "webdriver-manager"])
subprocess.check_call([sys.executable, "-m", "pip", "--disable-pip-version-check", "install", "telegraph"])


# ======================================================================
# ======================================================================


import traceback
import os
import argparse
import time
import logging
import logging.handlers
import urllib.request
import requests
import re

ACCESS_TOKEN = ""
CYBERDROP_TOKEN = ""
CYBERDROP_ALBUM = ""
CHAT_URL = "https://my_page"
RESERVED_FOLDERS = ['temp', '.idea', 'old', '.git', 'Old']
EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif", ".mp4")
VIDEO_EXTENSIONS = ".mp4"
HEADER_NAME = "My albums page"
WIDTH = 5000
HEIGHT = 5000
TOTAL_DIMENSION_THRESHOLD = 10000
DIMENSIONS_OVERWRITTEN = False
PAGE_SPECIFIED = False
DOWNLOAD_PAGE_SPECIFIED = False
DOWNLOAD_LIST_SPECIFIED = False
SIZE = 5000000
PAUSE = 2
DOMAIN = "https://telegra.ph"
LOG_FILE_NAME = "log.txt"
RESULTS_FILE_NAME = "results.txt"

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from telegraph import Telegraph
from PIL import Image
from urllib.parse import urlparse, urlunparse
import validators

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
    page=''
    page_down=''
    list_down=''


def setup_logger():
    handler_file = logging.handlers.WatchedFileHandler(os.environ.get("LOGFILE", LOG_FILE_NAME), encoding = 'utf8')
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
                os._exit(1)
        except TypeError:
            logger.fatal('Directory "' + str(__dir) + '" does not exist or not accessible.')
            os._exit(1)
    return True


def read_validate_input() -> ReadArgs:
    args = parse_input()

    if validate_file(args.list_down):
        global DOWNLOAD_LIST_SPECIFIED
        DOWNLOAD_LIST_SPECIFIED = True

    if validate_file(args.page_down):
        global DOWNLOAD_PAGE_SPECIFIED
        DOWNLOAD_PAGE_SPECIFIED = True

    if validate_file(args.page):
        global PAGE_SPECIFIED
        PAGE_SPECIFIED = True

    if not validate_folder(args.input_folder):
        args.input_folder = '.\\'
        args.output_folder = args.input_folder + '.\\old\\'
    else:
        if not validate_folder(args.output_folder):
            args.output_folder = args.input_folder + '\\old\\'

    if args.token is None or args.token == "":
        args.token = ACCESS_TOKEN
        if args.token is None or args.token == "":
            global should_create_account
            should_create_account = True

    if validate_natural(args.pause):
        global PAUSE
        PAUSE = args.pause

    width_set = False
    height_set = False
    if validate_natural(args.width):
        global WIDTH
        width_set = True
        WIDTH = args.width

    if validate_natural(args.height):
        global HEIGHT
        height_set = True
        HEIGHT = args.height

    if width_set or height_set:
        global DIMENSIONS_OVERWRITTEN
        DIMENSIONS_OVERWRITTEN = True
        if WIDTH * HEIGHT >= TOTAL_DIMENSION_THRESHOLD:
            logger.warning("======== Warning ========")
            logger.warning("The selected dimensions are greater than 10,000 pixels in total. The server will most likely reject these options.")
            logger.warning("")

    if validate_natural(args.size):
        global SIZE
        SIZE = args.size

    return args


def print_header(__args):
    logger.info('\n')
    logger.info('========================================================================')
    logger.info('========================================================================')
    logger.info('\n')
    logger.info('Starting in the directory: "' + os.getcwd() + '"')
    logger.info('Output directory:          "' + __args.output_folder + '"')
    logger.info('Upload pause:              ' + str(__args.pause) + ' seconds')

    if DIMENSIONS_OVERWRITTEN:
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


def validate_natural(_natural):
    return _natural is not None and _natural > 0


def parse_input():
    parser = argparse.ArgumentParser()
    parser.add_argument('-pa', '--page', help='↑ Upload existing html page from URL', type=str)
    parser.add_argument('-pd', '--page_download', help='↑ Download existing HTML page locally', type=str)
    parser.add_argument('-ld', '--list_download', help='↑ Download existing HTML pages locally from the list in the input text file', type=str)
    parser.add_argument('-i', '--input', help='↑ Input folder', type=str)
    parser.add_argument('-o', '--output', help='↑ Output folder', type=str)
    parser.add_argument('-t', '--token', help='↑ Account token', type=str)
    parser.add_argument('-p', '--pause', help='↑ Upload pause in seconds', type=int)
    parser.add_argument('-he', '--height', help='↑ Maximum image height', type=int)
    parser.add_argument('-wi', '--width', help='↑ Maximum image width', type=int)
    parser.add_argument('-s', '--size', help='← Maximum image file size', type=int)

    parser.error = parse_error

    args = None
    try:
        args = parser.parse_args()
    except TypeError:
        logger.info('')
        logger.info('')
        parser.print_help()
        os._exit(2)
        pass

    __args = ReadArgs()

    __args.token = args.token
    __args.pause = args.pause
    __args.input_folder = args.input
    __args.output_folder = args.output
    __args.height = args.height
    __args.width = args.width
    __args.size = args.size
    __args.page = args.page
    __args.page_down = args.page_download
    __args.list_down = args.list_download

    return __args


def parse_error(message):
    logger.fatal("Arguments are invalid:")
    logger.fatal("     " + str(message))
    logger.fatal("\n")

def get_available_server():
    try:
        headers = {'token': CYBERDROP_TOKEN}
        response = requests.get("https://cyberdrop.me/api/node", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                return data['url'].rstrip('/')
            else:
                logger.error("Failed to fetch available server: " + str(data))
        else:
            logger.error(f"Failed to get server, Status Code: {response.status_code}")
    except Exception as _e:
        logger.error(f"Error fetching available server: {_e}")
    return None


def get_direct_image_link(page_url, driver):
    try:
        driver.get(page_url)

        wait = WebDriverWait(driver, 20)
        download_btn = wait.until(ec.element_to_be_clickable((By.ID, 'downloadBtn')))
        wait.until(ec.element_attribute_to_include((By.ID, 'downloadBtn'), 'href'))

        direct_link = download_btn.get_attribute('href')

        # clean link has undefined behaviour
        # parsed_url = urlparse(direct_link)
        # direct_link = urlunparse(parsed_url._replace(query=''))

        if direct_link:
            return direct_link
        else:
            logger.error(f"Download link not found on page: {page_url}")

            # Save page source and screenshot
            timestamp = int(time.time())
            with open(f'debug_page_source_{timestamp}.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            driver.save_screenshot(f'debug_screenshot_{timestamp}.png')
            logger.info(f"Saved page source and screenshot for debugging.")

            return None

    except Exception as _e:
        logger.error(f"Error fetching direct image link from {page_url}: {_e}")
        return None


def upload_images(file_names, directory, errors):
    image_urls = []
    video_urls = []

    server_url = get_available_server()
    if server_url is None:
        logger.error("No server available. Exiting.")
        return [], []

    service = Service(ChromeDriverManager().install())

    chrome_options = Options()
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " \
                 "(KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')
    chrome_options.add_argument("--headless")
    chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        for file_name in file_names:
            upload_path = full_path = os.path.join(directory, file_name)

            logger.info("\nUploading: " + str(full_path))

            try:
                if not is_video_type(file_name):
                    if (not validate_image_dimensions(full_path)) or (not validate_file_size(full_path)):
                        upload_path = run_image_downgrade(full_path)
            except OSError as _e:
                logger.error("     The image " + file_name + " is corrupted. Will skip.\n     Error:   " + str(_e))
                errors.append(str(file_name) + ' : ' + str(e))
                continue

            try:                
                with open(upload_path, 'rb') as f:
                    files = {'files[]': f}
                    headers = {'token': CYBERDROP_TOKEN, 'albumid': CYBERDROP_ALBUM}
                    response = requests.post(f"{server_url}", headers=headers, files=files)
                    if response.status_code == 200:
                        data = response.json()
                        if data['success']:
                            page_url = data['files'][0]['url']
                            logger.info("Uploaded:  " + page_url)

                            direct_link = get_direct_image_link(page_url, driver)
                            if direct_link:
                                if is_video_type(file_name):
                                    video_urls.append(direct_link)
                                else:
                                    image_urls.append(direct_link)
                                logger.info("Direct image link obtained: " + str(direct_link))
                            else:
                                logger.error("Failed to obtain direct link for " + file_name)
                                errors.append(file_name + ' : Failed to obtain direct link')
                                continue
                        else:
                            error_msg = data.get('description', 'Unknown error')
                            logger.error("Upload failed for " + file_name + ": " + error_msg)
                            errors.append(file_name + ' : ' + error_msg)
                            continue
                    else:
                        logger.error("Failed to upload " + file_name + ". HTTP Status Code: " + str(response.status_code))
                        errors.append(file_name + ' : HTTP Status Code ' + str(response.status_code))
                        continue
            except Exception as _e:

                logger.error("     File " + file_name + " will be skipped.\n     Error:   " + str(_e))
                errors.append(str(file_name) + ' : ' + str(_e))

                logs = driver.get_log('browser')
                for entry in logs:
                    errors.append(f"Console Log: {entry}")
                continue

            move_image_to_output_folder(full_path, directory, file_name)

            try:
                if upload_path != full_path:
                    os.remove(upload_path)
                    logger.info("Temporary file " + str(upload_path) + " removed.")
            except IOError:
                pass

            time.sleep(PAUSE)

    finally:
        # Close chrome
        driver.quit()

    remove_uploaded_folder(directory)

    return image_urls, video_urls


def validate_file(__full_path):
    if __full_path is None or __full_path == "":
        return False
    else:
        return True


def validate_image_dimensions(__full_path):
    __im = Image.open(__full_path)
    __width, __height = __im.size

    if DIMENSIONS_OVERWRITTEN:
        return __width <= WIDTH and  __height <= HEIGHT
    else:
        return __width + __height < TOTAL_DIMENSION_THRESHOLD


def validate_file_size(full_path):
    __file_size = os.stat(full_path).st_size
    return True if __file_size < SIZE else False


def is_video_type(__file_name):
    return __file_name.lower().endswith(VIDEO_EXTENSIONS)


def run_image_downgrade(__full_path):
    __need_downscale = False

    if not validate_image_dimensions(__full_path):
        __need_downscale = True
        __need_downsize = True
    else:
        __need_downsize = not validate_file_size(__full_path)

    __trimmed_path = str(os.path.splitext(__full_path)[0])
    __im = Image.open(__full_path)

    if __need_downscale:
        __im = downscale(__im)

    if __need_downsize:
        return down_size(__im, __trimmed_path, os.stat(__full_path).st_size)

    else:
        __im.save(__trimmed_path + "_c.jpg", "JPEG", optimize=True, quality=100)
        logger.info("Temporary file saved to: " + str(__trimmed_path + "_c.jpg"))
        return __trimmed_path + "_c.jpg"


def down_size(__im, __trimmed_path, desired_size):
    logger.info("The image file size exceeds the desired value of " + str(desired_size))
    __compressed_path = compress_image(__trimmed_path, __im, desired_size)
    return __compressed_path


def downscale(__im):
    __width, __height = __im.size

    if not DIMENSIONS_OVERWRITTEN:
        logger.info("Image dimensions exceed the default limitation. (The sum of the width and height must not be greater than "
            + str(TOTAL_DIMENSION_THRESHOLD) + " px).")

        __new_width = int(__width * TOTAL_DIMENSION_THRESHOLD / float(__height + __width))
        __new_height = int(__height * TOTAL_DIMENSION_THRESHOLD / float(__height + __width))

    else:
        logger.info("Image dimensions exceed the specified boundaries of " + str(WIDTH)
            + " x " + str(HEIGHT) + " pixels (" + str(__width) + " x " + str(__height) + ")")

        _h_factor = HEIGHT / float(__height)
        _w_factor = WIDTH  / float(__width)

        _factor = min(_h_factor,_w_factor)

        __new_width = int(__width * _factor)
        __new_height = int(__height * _factor)


    __im = __im.resize((__new_width, __new_height), Image.LANCZOS)

    logger.info("The image resolution changed to " + str(__new_width) + " x " + str(__new_height))
    return __im


def compress_image(__trimmed_path, img, former_size):
    __quality = 100
    try:
        os.remove(__trimmed_path + "_c.jpg")
    except IOError as __e:
        pass

    __current_size = needed_size = former_size if former_size < SIZE else SIZE

    while __current_size + 1 > needed_size:
        logger.info("     Image size: " + str(__current_size))
        if __quality == 0:
            os.remove(__trimmed_path + "_c.jpg")
            logger.error("Error: File cannot be compressed below " + str(SIZE))
            break

        logger.info("     Trying compression ratio " + str(__quality))

        img.save(__trimmed_path + "_c.jpg", "JPEG", optimize=True, quality=__quality)

        __current_size = os.stat(__trimmed_path + "_c.jpg").st_size
        __quality -= 1

    logger.info("\n")
    logger.info("The resulting image size is " + str(__current_size))
    logger.info("Compression ratio: " + str(__quality))
    logger.info("Temporary file saved to: " + str(__trimmed_path + "_c.jpg"))
    logger.info("\n")

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


def create_page_body(image_urls, video_urls):
    body = '<p><a href="' + CHAT_URL + '" target="_blank">' + HEADER_NAME + '</a></p>\n'
    for _url in image_urls:
        body += " <img src='{}'/>".format(_url)
    for _url_v in video_urls:
        body += " <video src='{}' preload='auto' controls='controls'></video>".format(_url_v)
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

    image_urls, video_urls = upload_images(file_names, __set_directory, errors_list)

    print_errors(errors_list)

    content = create_page_body(image_urls, video_urls)
    post_link = post(__set_directory, content)
    logger.info('\n' + post_link + '\n\n')

    return post_link, len(image_urls) + len(video_urls)


def add_page_to_results(__set_name, __url, _count):
    f = open(RESULTS_FILE_NAME, "a", encoding = "utf-8")
    f.write(__set_name + ' : ' + str(_count) + ' : ' + __url + '\n')
    f.close()





def download_from_list():
    url_list = []
    try:
        url_list = open(read_args.list_down, "r")
        url_list = url_list.read().split("\n")
    except OSError:
        logger.error('URL list cannot be read')

    for url_str in url_list:
        if validators.url(url_str):
            download_page(url_str)


def download_page(page = ''):
    if page == '' or page is None:
        if (not DOWNLOAD_PAGE_SPECIFIED) or DOWNLOAD_LIST_SPECIFIED:
            return

        logger.info('Fetching ' + read_args.page_down)
        page = read_args.page_down

    body, title = read_web_page_from_url(page)
    title = get_name_from_url(page)

    if not check_or_create_folder(title):
        return

    image_urls = get_image_links_from_html(body)
    image_urls = list(map(lambda s: ['https://telegra.ph' + str(s), str(s).split(".")[-1]], image_urls))

    download_images(image_urls, title)


def get_name_from_url(page):
    name = page.split("/")[-1]
    name = name.strip()
    name = name.replace("-", " ")
    name = name.replace("  ", " ")
    name = name.replace("  ", " ")
    name = name.strip()
    return name


def read_web_page_from_url(page):
    f = urllib.request.urlopen(page)
    body = f.read().decode('utf-8')
    title_pat = re.compile(r'<title([^<]*)')
    title = 'Unknown'
    try:
        title = title_pat.findall(body)[0]
        title = title.replace('Telegraph', '')
        title = title.strip()
        title = title.strip('>')
        title = title.strip()
        title = title.strip('–')
        title = title.strip()

    except IndexError:
        logger.warning('There is no title. \'Unknown\' string will be used.')

    return body, title


def check_or_create_folder(name):
    try:
        if os.path.isdir(name) is False:
            os.mkdir(name)
            logger.info(' ')
            logger.info('Folder ' + name + ' created.')
        else:
            logger.warning('Folder ' + name + ' already exists.')

        return True

    except OSError:
        logger.error('Folder creation failed')
        return False


def get_image_links_from_html(body):
    pat = re.compile(r'<img [^>]*src="([^"]+)')
    image_urls = pat.findall(body)
    return image_urls


def recreate_page():
    body, title = read_web_page_from_url(read_args.page)

    image_urls = get_image_links_from_html(body)
    content = create_page_body(image_urls,[])
    post_link = post(title, content)
    logger.info('\n' + post_link + '\n\n')

def download_images(image_urls, path):
    img_num = 1
    for image_url in image_urls:
        logger.info(' ')
        logger.info('Downloading ' + str(image_url[0]))

        r = requests.get(image_url[0], allow_redirects=True)
        file_name = str(img_num).zfill(3) + '.' + str(image_url[1])
        with open(os.path.join(os.path.dirname(__file__), path, file_name), 'wb') as output_file:
            output_file.write(r.content)

        logger.info(file_name + ' written down.')

        img_num += 1
        time.sleep(PAUSE)


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

    if PAGE_SPECIFIED:
        recreate_page()

    elif DOWNLOAD_PAGE_SPECIFIED:
        download_page()

    elif DOWNLOAD_LIST_SPECIFIED:
        download_from_list()

    else:
        dirs_list = get_sub_dirs_list(read_args.input_folder)

        for set_directory in dirs_list:
            try:
                url, __count = elaborate_directory(set_directory)
                add_page_to_results(set_directory, url, __count)

            except BaseException as e:
                logger.fatal(set_directory + ' could not be uploaded.\nError: ' + str(e) + '\n' + str(traceback.format_exc()))

except SystemExit:
    os._exit(0)

except BaseException as e:
    logger.fatal("Critical error: " + str(e) + '\n' + str(traceback.format_exc()))
    os._exit(1)

os._exit(0)


