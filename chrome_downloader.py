import os
import requests
from tqdm import tqdm
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load the JSON file
with open('version-position-Android.json', 'r') as f:
    version_data = json.load(f)

# Define a function to download the file for each version
def download_file(version, position_id):
    # Construct the URL
    url = f"https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Android%2F{position_id}%2Fchrome-android.zip?alt=media"
    
    # Create a directory for the version
    directory = f"data/{version}"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Send a GET request to the URL
    response = requests.get(url, stream=True)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        print(f"Downloading {version}...")

        # Define the filename where the file will be saved
        filename = os.path.join(directory, "chrome-android.zip")

        # Get the total size of the file
        total_size_in_bytes = int(response.headers.get('content-length', 0))

        # Create a progress bar using tqdm to track the download progress
        with open(filename, 'wb') as f:
            for data in tqdm(response.iter_content(chunk_size=1024), total=total_size_in_bytes // 1024, unit='KB', desc=version):
                f.write(data)
        
        print(f"Download completed for {version} and saved as {filename}")
    else:
        print(f"Failed to download {version}, status code {response.status_code}")

# Define a function to process and download files concurrently using threads
def download_all_versions(version_data):
    # Define a ThreadPoolExecutor with a maximum number of workers (threads)
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        # Iterate over the version data and submit download tasks
        for version, position_id in version_data.items():
            # Stop processing if the version is "70.0.3499.0"
            if version == "70.0.3499.0":
                break

            # Submit the download task to the thread pool
            futures.append(executor.submit(download_file, version, position_id))

        # Wait for all tasks to complete and handle results
        for future in as_completed(futures):
            try:
                future.result()  # You can also handle exceptions here
            except Exception as e:
                print(f"Error occurred: {e}")

# Run the download process
download_all_versions(version_data)
