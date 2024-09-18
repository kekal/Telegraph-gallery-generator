
# coding=utf-8

import subprocess
import sys

# ======================================================================
# ======================================================================

subprocess.check_call([sys.executable, "-m", "pip", "--disable-pip-version-check", "install", "--upgrade", "Pillow==10.4.0"])
subprocess.check_call([sys.executable, "-m", "pip", "--disable-pip-version-check", "install", "--upgrade", "validators==0.34.0"])
subprocess.check_call([sys.executable, "-m", "pip", "--disable-pip-version-check", "install", "--upgrade", "requests==2.32.3"])
subprocess.check_call([sys.executable, "-m", "pip", "--disable-pip-version-check", "install", "--upgrade", "selenium==4.24.0", "webdriver-manager==4.0.2"])
subprocess.check_call([sys.executable, "-m", "pip", "--disable-pip-version-check", "install", "--upgrade", "telegraph==2.2.0"])

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


# =========== Do not change anything outside this block ===========

TELEGRAPH_ACCESS_TOKEN = ""

CYBERDROP_TOKEN = ""
CYBERDROP_ALBUM = ""

IMGBB_API = ""

AUTHOR_URL = "https://my_page"
HEADER_NAME = "My albums page"
WIDTH = 5000
HEIGHT = 5000
TOTAL_DIMENSION_THRESHOLD = 10000
SIZE = 5000000
PAUSE = 2

LOG_FILE_NAME = "log.txt"
RESULTS_FILE_NAME = "results.txt"

# =================================================================

TELEGRAPH_DOMAIN = "https://telegra.ph"
IMGBB_DOMAIN = "https://api.imgbb.com/1/upload"

RESERVED_FOLDERS = ['temp', '.idea', 'old', '.git', 'Old']
EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif", ".mp4")
VIDEO_EXTENSIONS = ".mp4"

DIMENSIONS_OVERWRITTEN = False
PAGE_SPECIFIED = False
DOWNLOAD_PAGE_SPECIFIED = False
DOWNLOAD_LIST_SPECIFIED = False


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from telegraph import Telegraph
from PIL import Image
# from urllib.parse import urlparse, urlunparse
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




class Utils:

    @staticmethod
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


    @staticmethod
    def validate_image_dimensions(__full_path):
        __im = Image.open(__full_path)
        __width, __height = __im.size

        if DIMENSIONS_OVERWRITTEN:
            return __width <= WIDTH and __height <= HEIGHT
        else:
            return __width + __height < TOTAL_DIMENSION_THRESHOLD

    @staticmethod
    def run_image_downgrade(__full_path):
        __need_downscale = False

        if not Utils.validate_image_dimensions(__full_path):
            __need_downscale = True
            __need_downsize = True
        else:
            __need_downsize = not FileSystem.validate_file_size(__full_path)

        __trimmed_path = str(os.path.splitext(__full_path)[0])
        __im = Image.open(__full_path)

        if __need_downscale:
            __im = Utils.downscale(__im)

        if __need_downsize:
            return Utils.down_size(__im, __trimmed_path, os.stat(__full_path).st_size)

        else:
            __im.save(__trimmed_path + "_c.jpg", "JPEG", optimize=True, quality=100)
            logger.info("Temporary file saved to: " + str(__trimmed_path + "_c.jpg"))
            return __trimmed_path + "_c.jpg"

    @staticmethod
    def down_size(__im, __trimmed_path, desired_size):
        logger.info("The image file size exceeds the desired value of " + str(desired_size))
        __compressed_path = Utils.compress_image(__trimmed_path, __im, desired_size)
        return __compressed_path

    @staticmethod
    def downscale(__im):
        __width, __height = __im.size

        if not DIMENSIONS_OVERWRITTEN:
            logger.info(
                "Image dimensions exceed the default limitation. (The sum of the width and height must not be greater than "
                + str(TOTAL_DIMENSION_THRESHOLD) + " px).")

            __new_width = int(__width * TOTAL_DIMENSION_THRESHOLD / float(__height + __width))
            __new_height = int(__height * TOTAL_DIMENSION_THRESHOLD / float(__height + __width))

        else:
            logger.info("Image dimensions exceed the specified boundaries of " + str(WIDTH)
                        + " x " + str(HEIGHT) + " pixels (" + str(__width) + " x " + str(__height) + ")")

            _h_factor = HEIGHT / float(__height)
            _w_factor = WIDTH / float(__width)

            _factor = min(_h_factor, _w_factor)

            __new_width = int(__width * _factor)
            __new_height = int(__height * _factor)

        __im = __im.resize((__new_width, __new_height), Image.Resampling.LANCZOS)

        logger.info("The image resolution changed to " + str(__new_width) + " x " + str(__new_height))
        return __im

    @staticmethod
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


    @staticmethod
    def print_errors(__errors):
        if len(__errors) > 0:
            logger.info("\nErrors list:")
            for err in __errors:
                logger.info("   " + err)


    @staticmethod
    def prepare_file_for_upload(file_name, directory, errors):
        full_path = os.path.join(directory, file_name)
        logger.info(f"Uploading: {full_path}")

        try:
            if not FileSystem.is_video_type(file_name):
                if not Utils.validate_image_dimensions(full_path) or not FileSystem.validate_file_size(full_path):
                    full_path = Utils.run_image_downgrade(full_path)
        except OSError as _e:
            logger.error(f"The image {file_name} is corrupted. Skipping. Error: {_e}")
            errors.append(f"{file_name} : {_e}")
            return None

        return full_path


    @staticmethod
    def parse_input():
        parser = argparse.ArgumentParser()
        parser.add_argument('-pa', '--page', help='↑ Upload existing html page from URL', type=str)
        parser.add_argument('-pd', '--page_download', help='↑ Download existing HTML page locally', type=str)
        parser.add_argument('-ld', '--list_download',
                            help='↑ Download existing HTML pages locally from the list in the input text file',
                            type=str)
        parser.add_argument('-i', '--input', help='↑ Input folder', type=str)
        parser.add_argument('-o', '--output', help='↑ Output folder', type=str)
        parser.add_argument('-t', '--token', help='↑ Account token', type=str)
        parser.add_argument('-p', '--pause', help='↑ Upload pause in seconds', type=int)
        parser.add_argument('-he', '--height', help='↑ Maximum image height', type=int)
        parser.add_argument('-wi', '--width', help='↑ Maximum image width', type=int)
        parser.add_argument('-s', '--size', help='← Maximum image file size', type=int)

        parser.error = Utils.parse_error

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

    @staticmethod
    def read_validate_input() -> ReadArgs:
        args = Utils.parse_input()

        if FileSystem.validate_file(args.list_down):
            global DOWNLOAD_LIST_SPECIFIED
            DOWNLOAD_LIST_SPECIFIED = True

        if FileSystem.validate_file(args.page_down):
            global DOWNLOAD_PAGE_SPECIFIED
            DOWNLOAD_PAGE_SPECIFIED = True

        if FileSystem.validate_file(args.page):
            global PAGE_SPECIFIED
            PAGE_SPECIFIED = True

        if not FileSystem.validate_folder(args.input_folder):
            args.input_folder = '.\\'
            args.output_folder = args.input_folder + '.\\old\\'
        else:
            if not FileSystem.validate_folder(args.output_folder):
                args.output_folder = args.input_folder + '\\old\\'

        if args.token is None or args.token == "":
            args.token = TELEGRAPH_ACCESS_TOKEN
            if args.token is None or args.token == "":
                args.token = None

        if Utils.validate_natural(args.pause):
            global PAUSE
            PAUSE = args.pause

        width_set = False
        height_set = False
        if Utils.validate_natural(args.width):
            global WIDTH
            width_set = True
            WIDTH = args.width

        if Utils.validate_natural(args.height):
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

        if Utils.validate_natural(args.size):
            global SIZE
            SIZE = args.size

        return args

    @staticmethod
    def parse_error(message):
        logger.fatal("Arguments are invalid:")
        logger.fatal("     " + str(message))
        logger.fatal("\n")


    @staticmethod
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

    @staticmethod
    def validate_natural(_natural):
        return _natural is not None and _natural > 0


class FileSystem:

    @staticmethod
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

    @staticmethod
    def validate_file(__full_path):
        if __full_path is None or __full_path == "":
            return False
        else:
            return True



    @staticmethod
    def validate_file_size(full_path):
        __file_size = os.stat(full_path).st_size
        return True if __file_size < SIZE else False

    @staticmethod
    def is_video_type(__file_name):
        return __file_name.lower().endswith(VIDEO_EXTENSIONS)

    @staticmethod
    def move_image_to_output_folder(__current_folder, __file_name):
        try:
            old_path = os.path.join(__current_folder, __file_name)
            old_folder = os.path.join(read_args.output_folder, __current_folder)

            if not os.path.exists(old_folder):
                os.makedirs(old_folder)

            os.replace(old_path, old_folder + '\\' + __file_name)
            logger.info(__file_name + ' was moved to the ' + old_folder)

        except BaseException as __e:
            logger.error("     " + str(__e) + '\n' + str(traceback.format_exc()))


    @staticmethod
    def remove_uploaded_folder(__directory):
        try:
            if not os.listdir(__directory):
                os.rmdir(__directory)
        except BaseException as __e:
            logger.error("     " + str(__e) + '\n' + str(traceback.format_exc()))

    @staticmethod
    def clean_up_file(upload_path, directory, file_name):
        FileSystem.move_image_to_output_folder(directory, file_name)

        try:
            if os.path.exists(upload_path):
                os.remove(upload_path)
                logger.info(f"Temporary file {upload_path} removed.")
        except IOError:
            pass

    @staticmethod
    def analyze_folder_content(__directory):
        logger.info("Searching for images...")
        __file_names = FileSystem.get_files_in_folder(__directory)
        for file_name in __file_names:
            logger.info("   " + file_name + " found")

        logger.info('\n   ' + str(len(__file_names)) + " files found.\n")

        return __file_names

    @staticmethod
    def get_files_in_folder(__working_directory):
        __files = [name for name in os.listdir(__working_directory) if
                   os.path.isfile(os.path.join(__working_directory, name))]

        return list(filter(lambda f: f.lower().endswith(EXTENSIONS), __files))

    @staticmethod
    def get_sub_dirs_list(root_folder):
        dirs = [name for name in os.listdir(root_folder) if os.path.isdir(os.path.join(root_folder, name))]

        return list(filter(lambda d: d not in RESERVED_FOLDERS, dirs))


class TelegraphRoutines:

    @staticmethod
    def create_or_attach_to_telegraph_account(token=None):
        if not token:
            __telegraph = Telegraph()
            __telegraph.create_account("Anonymous")
        else:
            __telegraph = Telegraph(access_token=token)

        logger.info("Currently used token: " + str(__telegraph.get_access_token()))
        return __telegraph

    @staticmethod
    def create_page_body(image_urls, video_urls):
        body = '<p><a href="' + AUTHOR_URL + '" target="_blank">' + HEADER_NAME + '</a></p>\n'
        for _url in image_urls:
            body += " <img src='{}'/>".format(_url)
        for _url_v in video_urls:
            body += " <video src='{}' preload='auto' controls='controls'></video>".format(_url_v)
        return body

    @staticmethod
    def post(__title, __body):
        response = telegraph.create_page(__title, html_content=__body)

        return '{}/{}'.format(TELEGRAPH_DOMAIN, response['path'])


class Cyberdrop:

    @staticmethod
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

    @staticmethod
    def get_direct_image_link(page_url, driver):
        try:
            driver.get(page_url)

            wait = WebDriverWait(driver, 20)
            download_btn = wait.until(ec.element_to_be_clickable((By.ID, 'downloadBtn')))
            wait.until(ec.element_attribute_to_include((By.ID, 'downloadBtn'), 'href'))

            direct_link = download_btn.get_attribute('href')

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

    @staticmethod
    def upload_file_to_cyberdrop(upload_path, server_url, errors):
        try:
            with open(upload_path, 'rb') as f:
                files = {'files[]': f}
                headers = {'token': CYBERDROP_TOKEN, 'albumid': CYBERDROP_ALBUM}
                response = requests.post(f"{server_url}", headers=headers, files=files)
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to upload file. HTTP Status Code: {response.status_code}")
                    errors.append(f"File upload failed: HTTP Status Code {response.status_code}")
                    return None
        except Exception as _e:
            logger.error(f"Error uploading file: {_e}")
            errors.append(f"File upload error: {_e}")
            return None

    @staticmethod
    def process_direct_link(page_url, driver, file_name, errors):
        direct_link = Cyberdrop.get_direct_image_link(page_url, driver)
        if direct_link:
            logger.info(f"Direct image link obtained: {direct_link}")
            return direct_link
        else:
            logger.error(f"Failed to obtain direct link for {file_name}")
            errors.append(f"{file_name} : Failed to obtain direct link")
            return None


    @staticmethod
    def upload_images_to_cyberdrop(file_names, directory, errors):
        image_urls, video_urls = [], []
        driver = Cyberdrop.setup_chrome_driver()

        try:
            server_url = Cyberdrop.get_available_server()
            if server_url is None:
                logger.error("No server available. Exiting.")
                return [], []

            for file_name in file_names:
                Cyberdrop.handle_image_upload_to_cyberdrop(file_name, directory, errors, driver, server_url, image_urls, video_urls)
                time.sleep(PAUSE)

        finally:
            driver.quit()

        FileSystem.remove_uploaded_folder(directory)
        return image_urls, video_urls

    @staticmethod
    def handle_image_upload_to_cyberdrop(file_name, directory, errors, driver, server_url, image_urls, video_urls):
        upload_path = Utils.prepare_file_for_upload(file_name, directory, errors)
        if upload_path is None:
            return

        response = Cyberdrop.upload_file_to_cyberdrop(upload_path, server_url, errors)
        if response is None:
            return

        page_url = Cyberdrop.extract_page_url_from_response(response, file_name, errors)
        if not page_url:
            return

        direct_link = Cyberdrop.process_direct_link(page_url, driver, file_name, errors)
        if direct_link:
            if FileSystem.is_video_type(file_name):
                video_urls.append(direct_link)
            else:
                image_urls.append(direct_link)

        FileSystem.clean_up_file(upload_path, directory, file_name)

    @staticmethod
    def setup_chrome_driver():
        service = Service(ChromeDriverManager().install())
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")

        # Set User-Agent (Optional)
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " \
                     "(KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
        chrome_options.add_argument(f'user-agent={user_agent}')

        # Set up logging preferences
        chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver

    @staticmethod
    def extract_page_url_from_response(response, file_name, errors):
        try:
            if response['success']:
                page_url = response['files'][0]['url']
                logger.info(f"Uploaded: {page_url}")
                return page_url
            else:
                error_msg = response.get('description', 'Unknown error')
                logger.error(f"Upload failed for {file_name}: {error_msg}")
                errors.append(f"{file_name} : {error_msg}")
                return None
        except Exception as _e:
            logger.error(f"Error extracting page URL from response for {file_name}: {_e}")
            errors.append(f"{file_name} : {_e}")
            return None

class Imgbb:

    @staticmethod
    def upload_file_to_imgbb(upload_path, errors):
        try:
            with open(upload_path, 'rb') as f:
                files = {'image': f}
                payload = {'key': IMGBB_API}
                response = requests.post(IMGBB_DOMAIN, files=files, data=payload)

                if response.status_code == 200:
                    return response.json()
                else:
                    error_detail = response.json().get('error', {}).get('message', 'No error message provided')
                    logger.error(f"Failed to upload file to imgbb. HTTP Status Code: {response.status_code} - {error_detail}")
                    errors.append(f"File upload failed to imgbb: HTTP Status Code {response.status_code} - {error_detail}")
                    return None
        except Exception as _e:
            logger.error(f"Error uploading file to imgbb: {_e}")
            errors.append(f"File upload error to imgbb: {_e}")
            return None

    @staticmethod
    def handle_image_upload_to_imgbb(file_name, directory, errors, image_urls, video_urls):
        upload_path = Utils.prepare_file_for_upload(file_name, directory, errors)
        if upload_path is None:
            return

        response = Imgbb.upload_file_to_imgbb(upload_path, errors)
        if response is None:
            return

        direct_link = Imgbb.process_direct_link_imgbb(response, file_name, errors)
        if direct_link:
            if FileSystem.is_video_type(file_name):
                video_urls.append(direct_link)
            else:
                image_urls.append(direct_link)

        FileSystem.clean_up_file(upload_path, directory, file_name)

    @staticmethod
    def process_direct_link_imgbb(response, file_name, errors):
        try:
            if response and 'data' in response and 'url' in response['data']:
                direct_link = response['data']['url']
                logger.info(f"Direct image link obtained from imgbb: {direct_link}")
                return direct_link
            else:
                error_msg = response.get('error', 'Unknown error from imgbb')
                logger.error(f"Failed to obtain direct link for {file_name} from imgbb: {error_msg}")
                errors.append(f"{file_name} : Failed to obtain direct link from imgbb")
                return None
        except Exception as _e:
            logger.error(f"Error processing direct image link from imgbb for {file_name}: {_e}")
            errors.append(f"{file_name} : {_e}")
            return None

    @staticmethod
    def upload_images_to_imgbb(file_names, directory, errors):
        image_urls, video_urls = [], []
        try:
            for file_name in file_names:
                Imgbb.handle_image_upload_to_imgbb(file_name, directory, errors, image_urls, video_urls)
                time.sleep(PAUSE)

        finally:
            FileSystem.remove_uploaded_folder(directory)

        return image_urls, video_urls


class ExistingPostRoutines:

    @staticmethod
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

    @staticmethod
    def recreate_page():
        body, title = ExistingPostRoutines.read_web_page_from_url(read_args.page)

        image_urls = get_image_links_from_html(body)
        content = TelegraphRoutines.create_page_body(image_urls, [])
        post_link = TelegraphRoutines.post(title, content)
        logger.info('\n' + post_link + '\n\n')

    @staticmethod
    def download_page(page=''):
        if page == '' or page is None:
            if (not DOWNLOAD_PAGE_SPECIFIED) or DOWNLOAD_LIST_SPECIFIED:
                return

            logger.info('Fetching ' + read_args.page_down)
            page = read_args.page_down

        body, title = ExistingPostRoutines.read_web_page_from_url(page)
        title = get_name_from_url(page)

        if not check_or_create_folder(title):
            return

        image_urls = get_image_links_from_html(body)
        image_urls = list(map(lambda s: ['https://telegra.ph' + str(s), str(s).split(".")[-1]], image_urls))

        ExistingPostRoutines.download_images(image_urls, title)

    @staticmethod
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

    @staticmethod
    def download_from_list():
        url_list = []
        try:
            url_list = open(read_args.list_down, "r")
            url_list = url_list.read().split("\n")
        except OSError:
            logger.error('URL list cannot be read')

        for url_str in url_list:
            if validators.url(url_str):
                ExistingPostRoutines.download_page(url_str)





def elaborate_directory(__set_directory):
    logger.info("\nWorking in directory " + __set_directory + "...\n")
    errors_list = []

    file_names = FileSystem.analyze_folder_content(__set_directory)

    # image_urls, video_urls = Cyberdrop.upload_images_to_cyberdrop(file_names, __set_directory, errors_list)
    image_urls, video_urls = Imgbb.upload_images_to_imgbb(file_names, __set_directory, errors_list)

    Utils.print_errors(errors_list)

    content = TelegraphRoutines.create_page_body(image_urls, video_urls)
    post_link = TelegraphRoutines.post(__set_directory, content)
    logger.info('\n' + post_link + '\n\n')

    return post_link, len(image_urls) + len(video_urls)


def add_page_to_results(__set_name, __url, _count):
    f = open(RESULTS_FILE_NAME, "a", encoding = "utf-8")
    f.write(__set_name + ' : ' + str(_count) + ' : ' + __url + '\n')
    f.close()







def get_name_from_url(page):
    name = page.split("/")[-1]
    name = name.strip()
    name = name.replace("-", " ")
    name = name.replace("  ", " ")
    name = name.replace("  ", " ")
    name = name.strip()
    return name





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



# ======================================================================
# ========================= Main routine ===============================
# ======================================================================

logger = Utils.setup_logger()


try:
    read_args = Utils.read_validate_input()

    os.chdir(read_args.input_folder)

    Utils.print_header(read_args)

    telegraph = TelegraphRoutines.create_or_attach_to_telegraph_account(read_args.token)

    if PAGE_SPECIFIED:
        ExistingPostRoutines.recreate_page()

    elif DOWNLOAD_PAGE_SPECIFIED:
        ExistingPostRoutines.download_page()

    elif DOWNLOAD_LIST_SPECIFIED:
        ExistingPostRoutines.download_from_list()

    else:
        dirs_list = FileSystem.get_sub_dirs_list(read_args.input_folder)

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
