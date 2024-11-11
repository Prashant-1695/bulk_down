import os
import subprocess
import requests

# Configuration
DOWNLOADS_FOLDER = os.path.expanduser("./Downloads")
ARIA2_PATH = "aria2c"  # Ensure 'aria2c' is in your PATH
GOFILE_API_URL = "https://store1.gofile.io/uploadFile"
LINKS_FILE = "links.txt"  # File containing URLs to download

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
        'parse_mode': 'Markdown'  # Optional: Use Markdown for formatting
    }
    response = requests.post(url, json=payload)
    if response.ok:
        print("Message sent to Telegram successfully.")
    else:
        print(f"Failed to send message: {response.status_code}, {response.text}")

def download_files_with_aria2(urls):
    """ Download multiple files using aria2. """
    ensure_directory_exists(DOWNLOADS_FOLDER)

    aria2_file = os.path.join(DOWNLOADS_FOLDER, "aria2_downloads.txt")

    with open(aria2_file, 'w') as f:
        for url in urls:
            f.write(url + '\n')

    # Send message indicating that downloads are starting
    send_telegram_message("Download started for the following files:\n" + "\n".join(urls))

    command = [ARIA2_PATH, '-i', aria2_file, '--dir', DOWNLOADS_FOLDER, '--continue']
    try:
        subprocess.run(command, check=True)
        print("All downloads initiated.")
        # Send message indicating that downloads are complete
        send_telegram_message("Download completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error downloading files: {e}")
        send_telegram_message("Error occurred during download.")

    return aria2_file

def upload_file(file_path):
    """ Upload the file to gofile.io. """
    if os.path.basename(file_path) == "aria2_downloads.txt":
        print(f"Skipping upload for: {file_path}")  # Skip uploading aria2_downloads.txt
        return None

    print(f"Attempting to upload: {file_path}")  # Debugging statement
    with open(file_path, 'rb') as f:
        response = requests.post(GOFILE_API_URL, files={'file': f})

    if response.ok:
        json_response = response.json()
        if json_response['status'] == 'ok':
            print(f"Uploaded {file_path} successfully. URL: {json_response['data']['downloadPage']}")
            return json_response['data']['downloadPage']  # Return the download link
        else:
            print(f"Failed to upload {file_path}: {json_response['message']}")
    else:
        print(f"Failed to upload {file_path} with status code {response.status_code}")
    return None

def read_urls_from_file(file_path):
    """ Read URLs from a text file. """
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def main():
    """ Main function to handle downloading and uploading. """
    urls_to_download = read_urls_from_file(LINKS_FILE)

    existing_files = {url.split("/")[-1]: os.path.join(DOWNLOADS_FOLDER, url.split("/")[-1])
                      for url in urls_to_download if os.path.exists(os.path.join(DOWNLOADS_FOLDER, url.split("/")[-1]))}

    urls_to_download = [url for url in urls_to_download if url.split("/")[-1] not in existing_files]

    aria2_file = None
    downloaded_files = []

    if urls_to_download:  # Check if there are any new downloads
        aria2_file = download_files_with_aria2(urls_to_download)
        downloaded_files.extend([url.split("/")[-1] for url in urls_to_download])
    else:
        print("All files already exist, no new downloads initiated.")

    # After downloading, upload all files in the Downloads folder
    if downloaded_files:
        send_telegram_message("Uploading files to gofile.io...")  # Notify that uploading is starting
        print("Uploading all files in the Downloads folder...")
        download_links = []
        for file_name in downloaded_files:
            file_path = os.path.join(DOWNLOADS_FOLDER, file_name)
            # Check if the file exists before attempting to upload
            if os.path.exists(file_path):
                download_link = upload_file(file_path)
                if download_link:
                    download_links.append(download_link)
            else:
                print(f"File not found, skipping upload: {file_path}")

        if download_links:
            send_telegram_message("Files uploaded successfully:\n" + "\n".join(download_links))
        else:
            send_telegram_message("No files were uploaded.")
    else:
        print("No files to upload.")

if __name__ == "__main__":
    main()
