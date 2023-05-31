import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import pandas as pd
from itertools import product

HTML = 'iplist.html'
HOST = 'https://iknowwhatyoudownload.com'
URL = 'https://iknowwhatyoudownload.com/en/peer/'
HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
}

def get_html(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        response.raise_for_status()
        return response.text
    except RequestException as e:
        print('An error occurred during the HTTP request:', e)
        return None

def get_ips(html):
    soup = BeautifulSoup(html, 'html.parser')
    div_elements = soup.select('div.padding-block')
    for div_element in div_elements:
        ip_links = div_element.select('a[href^="/en/peer/?ip="]')
        ip_addresses = [element.text for element in ip_links]
        if ip_addresses:
            return ip_addresses
            

def get_content(html, ip_address):
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.select('tr.danger, tr')
    extracted_data = []

    for item in items:
        try:
            title_element = item.select_one('td.name-column div.torrent_files a')
            category_element = item.select_one('td.category-column')
            link_element = item.select_one('div.torrent_files a')
            size_element = item.select_one('td.size-column')
            date_element = item.select_one('td.date-column')

            if all([title_element, category_element, link_element, size_element, date_element]):
                ext_data_element = soup.select('span.label.label-primary')
                ext_data = [element.get_text(strip=True) for element in ext_data_element]
                data = {
                    'ip': ip_address,
                    'title': title_element.get_text(strip=True),
                    'category': category_element.get_text(strip=True),
                    'link_torrent': HOST + link_element.get('href'),
                    'size': size_element.get_text(strip=True),
                    'date': date_element.get_text(strip=True),
                    'ext_data': ext_data
                }
                extracted_data.append(data)
        except Exception as e:
            print('An error occurred while extracting data:', e)

    return extracted_data


def save_doc(items, path):
    df_data = [
        [
            f"<span style='color:red'>{item[field]}</span>" if item['category'] == 'XXX' else item[field]
            for field in ['ip', 'title', 'category', 'link_torrent', 'size', 'date', 'ext_data']
        ]
        for item in items
    ]
    df_columns = ['IP', 'Name', 'Category', 'Torrent link', 'Size', 'Date', 'Ext. data']
    df = pd.DataFrame(df_data, columns=df_columns)

    try:
        with open(path, 'w', encoding='utf-8') as file:
            file.write(df.to_html(index=False, escape=False))
    except Exception as e:
        print('Error occurred while saving the table:', e)



def is_valid_mask(mask_choice):
    components = mask_choice.split('.')
    if len(components) != 4:
        return False
    for component in components:
        if component != '#' and (not component.isdigit() or int(component) > 255):
            return False
    return True

def is_valid_ip_address(ip_address):
    parts = ip_address.split('.')
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit() or not 0 <= int(part) <= 255:
            return False
    return True


def generate_ip_addresses(mask):
    parts = mask.split('.')
    indices = [i for i, part in enumerate(parts) if '#' in part]
    current_digits = [0] * len(indices)
    ip_info = []

    while True:
        ip_parts = parts[:]
        for index, digit in zip(indices, current_digits):
            ip_parts[index] = str(digit)
        ip_parts[-1] = '0'
        ip_address = '.'.join(ip_parts)
        html = get_html(URL)

        if not html:
            print('iknowwhatyoudownload.com is not currently available')
            break

        print("This IP is checked:", ip_address)
        html = get_html(URL + f'?ip={ip_address}')
        if html:
            ip_info.extend(get_content(html, ip_address))
            save_doc(ip_info, HTML)

            ips = get_ips(html)
            while True:
                try:
                    ip = ips[-1]
                    html = get_html(URL + f'?ip={ip}')
                    ips_temp = get_ips(html)
                    new_ips = [ip for ip in ips_temp if ip not in ips]
                    if not new_ips:
                        break
                    ips.extend(new_ips)
                except:
                    break
            if ips:
                for ip in ips:
                    html = get_html(URL + f'?ip={ip}')
                    print("This IP is checked:", ip)
                    if html:
                        ip_info.extend(get_content(html, ip))
            save_doc(ip_info, HTML)

        for i in range(len(current_digits) - 2, -1, -1):
            current_digits[i] += 1
            if current_digits[i] <= 255:
                break
            else:
                current_digits[i] = 0
        else:
            break



def check_single_ip():
    print('Enter the IP address to check:')
    ip = input('IP: ')
    while not is_valid_mask(ip):
        print('Invalid IP address. lease enter a valid IP address.')
        ip = input('IP: ')
    html = get_html(URL + f'?ip={ip}')
    if html:
        ip_info = get_content(html, ip)
        save_doc(ip_info, HTML)
        print('IP address checked successfully!')
    else:
        print('iknowwhatyoudownload.com is not currently available')


def check_ip_with_mask():
    print('Specify the IP address mask (e.g., 1.25.#.#): ')
    mask_choice = input('Mask: ')
    while not is_valid_mask(mask_choice):
        print('Invalid mask format. Please enter a valid mask.')
        mask_choice = input('Specify the IP address mask (e.g., 1.25.#.#): ')

    generate_ip_addresses(mask_choice)


def main():
    print('by Rizeru\n')

    while True:
        print('Menu:')
        print('1. Check a single IP address')
        print('2. Specify IP address mask')
        print('3. Quit')
        choice = input('Enter your choice (1-3): ')

        if choice == '1':
            check_single_ip()
        elif choice == '2':
            check_ip_with_mask()
        elif choice == '3':
            break
        else:
            print('Invalid choice. Please enter a valid choice.')

main()
