import os
import subprocess
import requests
import time

# Configuration
DOWNLOADS_FOLDER = os.path.expanduser("./Downloads")
SUB_FOLDER_NAME = "Love Game in Eastern Fantasy"  # Custom sub-folder name
ARIA2_PATH = "aria2c"  # Ensure 'aria2c' is in your PATH
LINKS_FILE = "links.txt"  # File containing URLs to download
ZIP_ENABLED = True  # Set this to True or False based on your requirement

# Get Telegram Bot Token and Chat ID from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def ensure_directory_exists(directory):
    """ Ensure that the given directory exists. Create it if it doesn't. """
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")

def send_telegram_message(message):
    """ Send a message to a Telegram chat. """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    response = requests.post(url, json=payload)
    if response.ok:
        print("Message sent to Telegram successfully.")
    else:
        print(f"Failed to send message: {response.status_code}, {response.text}")

def download_files_with_aria2(urls, download_dir):
    """ Download multiple files using aria2 and return failed downloads. """
    ensure_directory_exists(download_dir)

    aria2_file = os.path.join(download_dir, "aria2_downloads.txt")

    with open(aria2_file, 'w') as f:
        for url in urls:
            f.write(url + '\n')

    send_telegram_message(f"Download started for: {SUB_FOLDER_NAME}")

    command = [ARIA2_PATH, '-i', aria2_file, '--dir', download_dir, '--continue', '-x16']
    try:
        subprocess.run(command, check=True)
        print("All downloads initiated.")
        send_telegram_message("Download completed successfully.")
        return []  # No failed downloads
    except subprocess.CalledProcessError:
        print("Some downloads failed.")
        send_telegram_message("Some downloads failed. Attempting to re-download.")

    # Collect failed downloads
    failed_downloads = []
    for url in urls:
        file_name = os.path.join(download_dir, url.split("/")[-1])
        if not os.path.exists(file_name):
            failed_downloads.append(url)

    return failed_downloads

def read_urls_from_file(file_path):
    """ Read URLs from a text file. """
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def zip_folder(folder_path, zip_name):
    """ Zips the provided folder into a single zip file using p7zip. """
    print(f"Zipping folder: {folder_path} into {zip_name}")
    send_telegram_message("Started Zipping Folder...")

    start_time = time.time()  # Capture the start time
    command = ['7z', 'a', '-mx0', zip_name, folder_path]
    try:
        subprocess.run(command, check=True)
        elapsed_time = time.time() - start_time  # Calculate elapsed time
        print(f"Successfully created zip file: {zip_name}")
        print(f"Elapsed time for zipping: {elapsed_time:.2f} seconds")
        send_telegram_message(f"Zipping completed successfully in {elapsed_time:.2f} seconds.")
    except subprocess.CalledProcessError as e:
        print(f"Error creating zip file: {e}")

def main():
    """ Main function to handle downloading. """
    urls_to_download = read_urls_from_file(LINKS_FILE)

    # Create sub-folder for downloads
    sub_folder_path = os.path.join(DOWNLOADS_FOLDER, SUB_FOLDER_NAME)
    ensure_directory_exists(sub_folder_path)

    existing_files = {url.split("/")[-1]: os.path.join(sub_folder_path, url.split("/")[-1])
                      for url in urls_to_download if os.path.exists(os.path.join(sub_folder_path, url.split("/")[-1]))}

    urls_to_download = [url for url in urls_to_download if url.split("/")[-1] not in existing_files]

    if urls_to_download:
        failed_downloads = download_files_with_aria2(urls_to_download, sub_folder_path)

        # Retry failed downloads
        if failed_downloads:
            print("Retrying failed downloads...")
            failed_downloads = download_files_with_aria2(failed_downloads, sub_folder_path)

        if failed_downloads:
            print("Some downloads still failed after retrying.")
        else:
            print("All downloads completed successfully.")
    else:
        print("All files already exist, no new downloads initiated.")

    # Remove aria2_downloads.txt file if it exists
    aria2_file_path = os.path.join(sub_folder_path, "aria2_downloads.txt")
    if os.path.exists(aria2_file_path):
        os.remove(aria2_file_path)
        print(f"Removed temporary file: {aria2_file_path}")

    # Zip the sub-folder if ZIP_ENABLED is set to True
    if ZIP_ENABLED:
        zip_name = os.path.join(DOWNLOADS_FOLDER, SUB_FOLDER_NAME + '.7z')  # Custom zip file name with default extension
        zip_folder(sub_folder_path, zip_name)

if __name__ == "__main__":
    main()
