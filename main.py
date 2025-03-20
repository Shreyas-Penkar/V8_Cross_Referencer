import os
import json
import requests
from termcolor import colored
from bs4 import BeautifulSoup
from time import sleep
from concurrent.futures import ThreadPoolExecutor, as_completed

# Define URL parameters
os_list = ['Windows','Mac','Linux','iOS','Android']
channels = ['stable','beta','dev','canary']
path = 'db/'
failed_commits = []
cache_data = []


# Function to fetch the V8 version from the Chromium webpage
def fetch_v8_version(v8_commit_hash):
    url = f"https://chromium.googlesource.com/v8/v8.git/+/{v8_commit_hash}"
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        # Find the version from the <pre class="u-pre u-monospace MetadataMessage"> tag
        version_tag = soup.find('pre', {'class': 'u-pre u-monospace MetadataMessage'})
        if version_tag:
            # Extract the version number from the text
            version_text = version_tag.get_text(strip=True)
            if version_text.startswith("Version "):
                return version_text.split()[1]
    return None

def remove_all_files(directory):
    # Check if the directory exists
    if os.path.exists(directory):
        # List all files in the directory
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            
            # Only remove files (ignore subdirectories)
            if os.path.isfile(file_path):
                os.remove(file_path)  # Remove the file
    else:
        print(colored(f"[-] The directory {directory} does not exist.",'red'))

# Define the cache file path
CACHE_DIR = "cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def load_cache():
    global cache_data
    """ Load the cached V8 versions from a JSON file. """
    cache_file = os.path.join(CACHE_DIR, "v8_cache.json")
    if os.path.exists(cache_file):
        f = open(cache_file, 'r')
        data = json.load(f)
        f.close()
        return data
    return {}

def save_cache():
    global cache_data

    """ Save the V8 versions cache to a JSON file. """
    cache_file = os.path.join(CACHE_DIR, "v8_cache.json")
    f = open(cache_file, 'w')
    json.dump(cache_data, f, indent=4)
    f.close()

def fetch_v8_version_from_cache(v8_commit_hash):
    """ Check if V8 version exists in cache. """
    global cache_data
    return cache_data.get(v8_commit_hash)

def process_json_file(file_path, versions):
    """ Process a single JSON file with caching. This is the function executed by each thread. """
    global cache_data, failed_commits
    # Load the cache
    cache_data = load_cache()

    try:
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
            for entry in data:
                v8_commit_hash = entry.get("hashes", {}).get("v8")
                os_platform = entry.get("platform")
                channel = entry.get("channel")
                chrome_version = entry.get("version")

                if v8_commit_hash:
                    # Check if the V8 version is already cached
                    v8_version = fetch_v8_version_from_cache(str(v8_commit_hash))
                    
                    if v8_version is None:
                        # If not cached, fetch it and cache it
                        v8_version = fetch_v8_version(str(v8_commit_hash))
                        sleep(1)
                        if v8_version:
                            # Save the V8 version in cache
                            cache_data[v8_commit_hash] = v8_version
                            
                        else:
                            print(colored(f"[WARNING] V8 version not found for commit {v8_commit_hash} in {file_path}", 'yellow'))
                            failed_commits.append(v8_commit_hash)
                            continue

                    # Append the result to versions list
                    versions.append({
                        "OS": os_platform,
                        "channel": channel,
                        "chrome_version": chrome_version,
                        "v8_version": v8_version
                    })
                else:
                    print(colored(f"[WARNING] No V8 commit hash found in {file_path}", 'yellow'))
                    continue
    except json.JSONDecodeError:
        print(colored(f"[-] Error reading {file_path}. Skipping...", 'red'))

def process_json_files():
    global cache_data
    versions = []  # List to hold the version information
    directory_path = path

    # Get all the JSON file paths
    file_paths = [os.path.join(directory_path, filename) for filename in os.listdir(directory_path) if filename.endswith(".json")]

    # Create a ThreadPoolExecutor to process files in parallel
    # with ThreadPoolExecutor() as executor:
    #     futures = [executor.submit(process_json_file, file_path, versions) for file_path in file_paths]

    #     # Wait for all threads to complete
    #     for future in as_completed(futures):
    #         future.result()  # This will re-raise any exception that occurred in the thread
    
    for file_path in file_paths:
        process_json_file(file_path,versions)
        # sleep(0.2)

    save_cache()  # Update the cache file
    # Save the extracted data to a new JSON file
    with open(directory_path + 'versions.json', 'w') as output_file:
        json.dump(versions, output_file, indent=4)

    print(colored(f"[+] Success! All Versions Data has been saved to 'versions.json'.",'green'))

def load_versions_data():
    global path
    """ Load the versions data from the 'versions.json' file """
    try:
        with open(path+"versions.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print(colored("[-] versions.json file not found.",'red'))
        return []
    except json.JSONDecodeError:
        print(colored("[-] Error decoding JSON from versions.json.",'red'))
        return []

def print_table(entries,flag):
    # Calculate the maximum width of each column
    keyword = ''

    if flag == 'v8_version':
        keyword = 'V8'
    elif flag == 'chrome_version':
        keyword = 'Chrome'

    max_os_width = max(len(entry['OS']) for entry in entries)
    max_channel_width = max(len(entry['channel']) for entry in entries)
    max_chrome_version_width = max(len(entry[flag]) for entry in entries)
    
    
    # Print the header with proper alignment
    print(f"{'OS'.ljust(max_os_width)} \t{'Channel'.ljust(max_channel_width)} \t{keyword+' Version'.ljust(max_chrome_version_width)}")
    print("-" * (max_os_width + max_channel_width + max_chrome_version_width + 24))  # 6 is for the extra space between columns

    # Print the table rows with proper alignment
    for entry in entries:
        print(f"{entry['OS'].ljust(max_os_width)} \t{entry['channel'].ljust(max_channel_width)} \t\t{entry[flag].ljust(max_chrome_version_width)}")


def get_v8_from_chrome_version():
    versions_data = load_versions_data()
    if not versions_data:
        print(colored("[-] Lookup Failed! Check for any issues!",'red'))
        return

    chrome_version = input("Enter Chrome version (e.g., 91.0.4472.124): ")

    # Filter the data for matching Chrome version
    matching_entries = [entry for entry in versions_data if entry["chrome_version"] == chrome_version]

    if matching_entries:
        print(colored(f"\n[+] Found {len(matching_entries)} entries for Chrome version {chrome_version}:",'red'))
        print()
        print_table(matching_entries,'v8_version')
    else:
        print(colored(f"[-] No entries found for Chrome version {chrome_version}.",'red'))

def get_chrome_from_v8_version():
    versions_data = load_versions_data()
    if not versions_data:
        print(colored("[-] Lookup Failed! Check for any issues!",'red'))
        return

    v8_version = input("Enter V8 version (e.g., 13.6.82): ")

    # Filter the data for matching V8 version
    matching_entries = [entry for entry in versions_data if entry["v8_version"] == v8_version]

    if matching_entries:
        print(colored(f"\n[+] Found {len(matching_entries)} entries for V8 version {v8_version}:",'red'))
        print()
        print_table(matching_entries,'chrome_version')
    else:
        print(colored(f"[-] No entries found for V8 version {v8_version}.",'red'))

def fetch_and_save_data(os, channel):
    global path
    url = f"https://chromiumdash.appspot.com/fetch_releases?num=1000000&platform={os}&channel={channel}"
    
    try:
        # Create a session object for reusing the connection
        print(colored(f"[*] Fetching Data for {os}-{channel} ...",'yellow'))

        with requests.Session() as session:
            # Send the GET request
            response = session.get(url)
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx, 5xx)
            
            # Parse and save JSON data
            data = response.json()
            file_path = f"{path}{os}_{channel}.json"
            
            with open(file_path, 'w') as json_file:
                json.dump(data, json_file, indent=4)
            
            print(colored(f"[+] Success! JSON data has been saved to {file_path}",'green'))
    
    except requests.exceptions.RequestException as e:
        print(colored(f"[-] Error fetching data for {os}_{channel}: {e}",'red'))


def update_db():
    global path, os_list, channels, failed_commits
    remove_all_files(path)
    print(colored("[*] Updating Chrome/V8 Versions DB...",'yellow'))
    with ThreadPoolExecutor() as executor:
        # Submit tasks to the ThreadPoolExecutor
        futures = []
        for os in os_list:
            for channel in channels:
                futures.append(executor.submit(fetch_and_save_data, os, channel))

        # Wait for all the tasks to complete
        for future in futures:
            future.result()  # This will re-raise any exception that occurred in the thread
    print(colored("[*] Processing all data and updating final DB...",'yellow'))
    process_json_files()
    print(failed_commits)

def display_menu():
    print(colored("\nMenu:",'magenta'))
    print(colored("1. Get V8 version from Chrome Version",'magenta'))
    print(colored("2. Get Chrome version from V8 Version",'magenta'))
    print(colored("3. Update DB",'magenta'))
    print(colored("4. Exit",'magenta'))

def main():
    while True:
        display_menu()
        
        choice = input("Enter your choice (1/2/3/4): ")
        
        if choice == '1':
            get_v8_from_chrome_version()
        elif choice == '2':
            get_chrome_from_v8_version()
        elif choice == '3':
            update_db()
        elif choice == '4':
            print(colored("Bye :)",'magenta'))
            break
        else:
            print(colored("[-] Invalid choice. Please try again."),'red')

main()
