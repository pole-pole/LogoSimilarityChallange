import os
import requests
import pandas as pd
import re
from multiprocessing.dummy import Pool as ThreadPool
from urllib.parse import urlparse
from PIL import Image
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
import asyncio


requests.packages.urllib3.disable_warnings()

database_file = 'database.csv'
database = pd.read_csv(database_file)

#convert column types
database = database.astype('object')

HTML_FOLDER = 'html_files'
LOGO_FOLDER = 'logos'
THREADS = 30  # Number of threads to use

# Configure browser for crawl4AI
browser_config = BrowserConfig(
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    headless=True,
    use_persistent_context=True,  # For cookie persistence [3][4]
    user_data_dir="./browser_data",  # Recommended for cookies [3]
    java_script_enabled=True,  # Default is True [3]
    ignore_https_errors=True,
    accept_downloads=True
    )

run_config = CrawlerRunConfig(
    magic=True,
    simulate_user=True,
    override_navigator=True
    )

# Header for the simple HTTP request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# Function to get the HTML of a web page
async def crawl_page(item):

    link = item['domain_link']
    response_code = 0

    async with AsyncWebCrawler() as crawler:
        # Perform the crawl
        response = await crawler.arun(url=link, config=run_config)
        response_code = response.status_code

        if response_code is None or (response_code != 200):
            link = link.replace('https://', 'https://www.')
            response = await crawler.arun(url=link, config=run_config)
            response_code = response.status_code

        if response_code is None:
            response_code = 999

    item['status_code'] = response_code

    if response_code == 200:
        item['page_crawl_error'] = ''
        return {'updated_row': item, 'html': response.html, 'message': "We got a page"}
    else:
        item['page_crawl_error'] = response.error_message
        return {'updated_row': item, 'html': '', 'message': 'We could not get a page'}


# Function that tries to find a logo using regex - it looks for the first image containing 'logo' in filename
def find_logo_src(html_content):
    img_pattern = re.compile(r'<img[^>]*?src=([\'"])(.*?)\1', re.IGNORECASE)
    for match in img_pattern.findall(html_content):
        src = match[1]
        if re.search(r'/([^/]*logo[^/]*)(?:[?#]|$)', src, re.IGNORECASE):
            return src
    return None

#Function to request a logo image
def get_logo(link, item):

    if item['requires_www']:
        request_url = link.replace('https://', 'https://www.')
    else:
        request_url = link

    try:
        response_logo = requests.get(request_url, headers=headers, timeout=10, verify=False)
        status_code = response_logo.status_code

    except requests.RequestException as e:  # Catch any other exceptions
        item['logo_scrape_error'] = f"Other error: {e}"
        status_code = 909

    # sometimes we get around HTTP errors by trying with www.
    if status_code != 200 and '://www.' not in request_url:
        request_url = request_url.replace('://', '://www.')
        try:
            response_logo = requests.get(request_url, headers=headers, timeout=10, verify=False)
            status_code = response_logo.status_code
        except requests.RequestException as e:  # Catch any other exceptions
            item['logo_scrape_error'] = f"Other error: {e}"
            status_code = 909

    # we received somthing...
    if status_code == 200:
        item['logo_scrape_error'] = ''
        filetype = get_file_extension(request_url)
        if filetype == '':
            filetype = '.svg'

        with open(os.path.join(LOGO_FOLDER, f"{item['id']}{filetype}"), 'wb') as f:
            f.write(response_logo.content)

        if filetype == '.svg':
            if (is_svg(f"{LOGO_FOLDER}/{item['id']}{filetype}")):
                item['logo_image_type'] = 'svg'
                item['logo_is_image'] = True
            else:
                item['logo_is_image'] = False
        else:
            try:
                # Open the file as an image
                with Image.open(f"{LOGO_FOLDER}/{item['id']}{filetype}") as img:
                    item['logo_image_type'] = img.format
                    item['logo_is_image'] = True
            except IOError:
                item['logo_is_image'] = False

    return item


# Function to get the file extension of a file from an URL
def get_file_extension(url):
    parsed_url = urlparse(url)
    path = parsed_url.path
    return os.path.splitext(path)[1]

#Function to check if a file is a valid SVG (because image libraries do not do this)
def is_svg(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read(500).strip()
            return content.startswith("<svg") or "<svg" in content
    except Exception:
        return False

# Main function - process a domain
def process_row(domain_id):
    # we get the row and make it a dictionary
    row = to_crawl.loc[to_crawl['id'] == domain_id]
    row_values = row.iloc[0].to_dict()

    crawl_result = asyncio.run(crawl_page(row_values))
    row_values = crawl_result['updated_row']

    #print(f"{row_values['id']} - {crawl_result['message']}")


    if row_values['status_code'] == 200:
        # we write the html to a file
        with open(os.path.join(HTML_FOLDER, f"{row_values['id']}.html"), 'w', encoding='utf-8') as f:
            f.write(crawl_result['html'])

        #we try to find the logo
        logo_src = find_logo_src(crawl_result['html'])
        #print(f"{row_values['id']} -- {logo_src}")

        if logo_src is not None:
            row_values['logo_found'] = True
            row_values['logo_src'] = logo_src
            if logo_src.startswith('//'):
                row_values['logo_link'] = f"https:{logo_src}"
            elif logo_src.startswith(('http://', 'https://')):
                row_values['logo_link'] = logo_src
            else:
                row_values['logo_link'] = f"https://{row_values['domain']}/{logo_src.lstrip('/').replace("../", "")}"

            #now we try to get the logo
            row_values = get_logo(row_values['logo_link'], row_values)
        else:
            row_values['logo_found'] = False

    #print(row_values)

    #update the dataframe
    for column, value in row_values.items():
        if column != 'id':
            to_crawl.loc[to_crawl['id'] == row_values['id'], column] = value

    return


# select rows that have status code different from 200
#to_crawl = database.loc[database['status_code'] != 200]
to_crawl = database.loc[database['logo_is_image'] != True ]
ids_to_crawl = to_crawl['id'].tolist()
print(f"Crawling {len(ids_to_crawl)} pages. ")

pool = ThreadPool(THREADS)
results = pool.map(process_row, ids_to_crawl)

pool.close()
pool.join()

to_crawl.set_index('id', inplace=True)
database.set_index('id', inplace=True)
database.update(to_crawl)

database.to_csv(database_file, index=False)