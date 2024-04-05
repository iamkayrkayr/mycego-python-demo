from colorama import Fore, Style
import hashlib
import math
import os
from pathlib import Path
from PIL import Image
import requests
import shutil
import sys
import urllib.parse

##
# Variables
##

yandex_disk_root_public_key = 'https://disk.yandex.ru/d/V47MEP5hZ3U1kg'
cloud_api_base_url = 'https://cloud-api.yandex.net/v1/disk/public/resources'
cache_dir_path = 'cached'
#
collage_out_file_path = 'Result.tif'

# By default values from the example are taken
collage_params = {
    # set cols_count to None to get a grid as close to square as possible
#     'cols_count': None,

    # bg_color: collage background color: (R, G, B) or string
#     'bg_color': 'white',

#     'thumb_width': 192,
#     'thumb_height': 192,
#     'pad_left': 74,
#     'pad_right': 74,
#     'gap_x': 28,
#     'pad_top': 96,
#     'pad_bottom': 96,
#     'gap_y': 24,
}

# Read stdin arguments
if len(sys.argv) > 1:
    first_stdin_arg = sys.argv[1]
    if first_stdin_arg.isdigit():
        first_stdin_arg = int(first_stdin_arg)
        if first_stdin_arg > 0:
            collage_params['cols_count'] = first_stdin_arg

##
# Functions
##

def print_comment(text):
    print(Fore.YELLOW + text + Style.RESET_ALL)

def print_success(text):
    print(Fore.GREEN + text + Style.RESET_ALL)

def print_error(text):
    print(Fore.RED + text + Style.RESET_ALL)

##
# Fetch details of the directories from which images should be taken.
#
def fetch_dirs_list():
    fetch_dirs_list_url = cloud_api_base_url + '?' + urllib.parse.urlencode({
        'public_key': yandex_disk_root_public_key
    })
    fetch_dirs_list_response = requests.get(fetch_dirs_list_url)
    if (fetch_dirs_list_response.status_code != 200):
        sys.exit('Error fetching directories list: status ' + str(fetch_dirs_list_response.status_code))

    return fetch_dirs_list_response.json()['_embedded']['items']

##
# Print directories names and ask user to choose.
#
def request_dirs_input(dirs_list):
    print_success('List of directories:')
    for dir_index in range(len(dirs_list)):
        print(str(dir_index) + ': ' + dirs_list[dir_index]['name'])

    print_comment(
        'Enter numbers list separated by commas. ' +
        'For each number images from the corresponding directory will be included\nEnter "q" to exit'
    )
    selected_dirs = []
    for line in sys.stdin:
        selected_dirs = []
        clean_line = line.rstrip()
        if clean_line == 'q':
            sys.exit()
        selected_indices = clean_line.split(',')

        if len(selected_indices) == 0: continue

        has_invalid_input = False
        for selected_index_str in selected_indices:
            if selected_index_str.isdigit():
                selected_index = int(selected_index_str)
                if 0 <= selected_index < len(dirs_list):
                    selected_dirs.append(dirs_list[selected_index])
                    continue
            has_invalid_input = True

        if (len(selected_indices) > 0) and (not has_invalid_input):
            break

        print_error('Invalid input: not an index or out of range')

    return selected_dirs

##
# Fetch details of the images from the picked directories.
#
def fetch_files_list(selected_dirs):
    print_comment('Fetching files list ...')

    selected_files = []
    for dir_data in selected_dirs:
        fetch_files_list_url = cloud_api_base_url + '?' + urllib.parse.urlencode({
            'public_key': yandex_disk_root_public_key,
            'path': dir_data['path']
        })
        fetch_files_list_response = requests.get(fetch_files_list_url)
        if (fetch_files_list_response.status_code != 200):
            sys.exit('Error fetching images: status ' + str(fetch_files_list_response.status_code))

        files_list = fetch_files_list_response.json()['_embedded']['items']
        selected_files += files_list

    return selected_files

##
# Download images
#
def cache_selected_images(selected_files):
    # to remove cache
    # if os.path.exists(cache_dir_path) and os.path.isdir(cache_dir_path):
    #     shutil.rmtree(cache_dir_path)
    Path(cache_dir_path).mkdir(parents=True, exist_ok=True)

    cached_images_paths = []
    print_comment('Preparing ' + str(len(selected_files)) + ' files ...')
    for image_details in selected_files:
        image_cache_key = image_details['path'] + '|' + image_details['modified']
        tmp_file_name = hashlib.sha256(image_cache_key.encode('utf-8')).hexdigest()
        tmp_file_path = cache_dir_path + '/' + tmp_file_name

        if os.path.exists(tmp_file_path) and os.path.isfile(tmp_file_path):
            print_comment('Image ' + image_details['path'] + ': using cached version')
        else:
            fetch_image_url = image_details['sizes'][0]['url']
            download_image_response = requests.get(fetch_image_url, stream=True)
            if (download_image_response.status_code != 200):
                sys.exit('Error downloading image: status ' + str(download_image_response.status_code))

            with open(tmp_file_path, 'wb') as out_file:
                shutil.copyfileobj(download_image_response.raw, out_file)
            print_success('Image ' + image_details['path'] + ' is downloaded')

        cached_images_paths.append(tmp_file_path)

    return cached_images_paths

##
# Compose collage and save it in the file
#
def compose_collage(
    cached_images_paths,
    collage_params
):
    cols_count = collage_params.get('cols_count', None)
    bg_color = collage_params.get('bg_color', 'white')
    thumb_width = collage_params.get('thumb_width', 192)
    thumb_height = collage_params.get('thumb_height', thumb_width)
    pad_left = collage_params.get('pad_left', 74)
    pad_right = collage_params.get('pad_right', pad_left)
    gap_x = collage_params.get('gap_x', 28)
    pad_top = collage_params.get('pad_top', 96)
    pad_bottom = collage_params.get('pad_bottom', pad_top)
    gap_y = collage_params.get('gap_y', 24)

    thumbs_count = len(cached_images_paths)
    cols_count = cols_count or math.ceil(math.sqrt(thumbs_count))
    rows_count = math.ceil(thumbs_count / cols_count)

    collage_width = pad_left + thumb_width * cols_count + gap_x * (cols_count - 1) + pad_right
    collage_height = pad_top + thumb_height * rows_count + gap_y * (rows_count - 1) + pad_bottom
    collage_img = Image.new('RGB', (collage_width, collage_height), bg_color)

    for image_index in range(len(cached_images_paths)):
        image_path = cached_images_paths[image_index]
        img = Image.open(image_path)

        img.thumbnail((thumb_width, thumb_height))

        position_x = image_index % cols_count
        position_y = math.floor(image_index / cols_count)
        offset_x = pad_left + (thumb_width + gap_x) * position_x
        offset_y = pad_top + (thumb_height + gap_y) * position_y

        collage_img.paste(img, (offset_x, offset_y))

        del img

    collage_img.save(collage_out_file_path)
    del collage_img

    print_success('Collage is saved: ' + collage_out_file_path)

def main():
    dirs_list = fetch_dirs_list()
    selected_dirs = request_dirs_input(dirs_list)
    selected_files = fetch_files_list(selected_dirs)
    cached_images_paths = cache_selected_images(selected_files)
    compose_collage(
        cached_images_paths,
        collage_params,
    )

##
# Execution
##

main()
