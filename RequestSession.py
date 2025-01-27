import requests
from bs4 import BeautifulSoup
import os
from http import cookiejar

PROXY_FILE = 'working_proxy.txt'

urls = [
    'https://free-proxy-list.net/',
    'https://www.sslproxies.org/',
    'https://www.us-proxy.org/',
]

def createSession(userAgent=None,headers={},local_storage=None ,cookies=None, proxy=False, tor = False):

    s = requests.Session()

    if userAgent is not None : s.headers.update({"user-agent": userAgent})

    if  cookies is not None and tor is False:
        if isinstance(cookies,cookiejar.CookieJar):
            s.cookies.update(cookies)
        elif isinstance(cookies,list):
            for cookie in cookies:
                s.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])

    if local_storage:
        for key, value in local_storage:
            headers[key] = value

    if headers:
        s.headers.update(headers)

    if proxy is True and tor is False:
        
        proxies = get_proxies(urls)
       
        working_proxy = find_working_proxy(proxies)
        if working_proxy:
            
            print(f'New working proxy found and saved: {working_proxy}')
        else:
            print('No working proxy found.')
            
        s.proxies.update({
                'http': working_proxy,
            })
        
    if tor:
        for cookie in cookies:
            host, name, value, path, expiry, *extra = cookie            
            s.cookies.set(name, value, domain=host, path=path, expires=expiry)
            
        proxies = {
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050'  
        }
        s.proxies.update(proxies)

    
    return s

def get_proxies(urls):
    proxies = []
    for url in urls:
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            table = soup.find('table', class_='table table-striped table-bordered')
            for row in table.tbody.find_all('tr'):
                ip = row.find_all('td')[0].text
                port = row.find_all('td')[1].text
                proxy = f'http://{ip}:{port}'
                proxies.append(proxy)
        except Exception as e:
            print(f"Error fetching proxies from {url}: {e}")
    return proxies

def check_proxy(proxy):
    try:
        response = requests.get('http://httpbin.org/ip', proxies={'http': proxy, 'https': proxy}, timeout=5)
        if response.status_code == 200:
            # Check if the IP address in the response matches the proxy IP
            response_ip = response.json()['origin']
            proxy_ip = proxy.split('://')[1].split(':')[0]

            print("checking proxy == response : ", response_ip)
            return response_ip == proxy_ip
    except requests.RequestException:
        return False
    return False

def find_working_proxy(proxies):
    for proxy in proxies:
        if check_proxy(proxy):
            return proxy
    return None

def save_proxy(proxy):
    with open(PROXY_FILE, 'w') as file:
        file.write(proxy)

def load_saved_proxy():
    if os.path.exists(PROXY_FILE):
        with open(PROXY_FILE, 'r') as file:
            return file.read().strip()
    return None
