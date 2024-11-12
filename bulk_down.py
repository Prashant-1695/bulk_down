import os
import subprocess
import requests
import time  # Import time module for measuring upload duration

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
    """ Upload the file to gofile.io and calculate upload speed in MB/s. """
    if os.path.basename(file_path) == "aria2_downloads.txt":
        print(f"Skipping upload for: {file_path}")  # Skip uploading aria2_downloads.txt
        return None

    # Notify that the upload is starting
    send_telegram_message(f"Starting upload for: {file_path}")
    print(f"Attempting to upload: {file_path}")  # Debugging statement

    # Get file size for speed calculation
    file_size = os.path.getsize(file_path)  # Size in bytes

    start_time = time.time()  # Start time measurement
    with open(file_path, 'rb') as f:
        response = requests.post(GOFILE_API_URL, files={'file': f})

    # Calculate the duration of the upload
    duration = time.time() - start_time  # Duration in seconds

    if response.ok:
        json_response = response.json()
        if json_response['status'] == 'ok':
            download_link = json_response['data']['downloadPage']
            print(f"Uploaded {file_path} successfully. URL: {download_link}")

            # Calculate upload speed in MB/s
            upload_speed = (file_size / 1024 / 1024) / duration if duration > 0 else 0  # Convert bytes to MB
            print(f"Upload Speed: {upload_speed:.2f} MB/s")

            return download_link  # Return the download link
        else:
            print(f"Failed to upload {file_path}: {json_response['message']}")
    else:
        print(f"Failed to upload {file_path} with status code {response.status_code}")
    return None

def read_urls_from_file(file_path):
    """ Read URLs from a text file. """
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def get_video_files(folder):
    """ Get a list of video files in the given folder. """
    video_extensions = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.mpeg', '.mpg')
    return [f for f in os.listdir(folder) if f.endswith(video_extensions)]

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

    # After downloading, upload all video files in the Downloads folder
    video_files = get_video_files(DOWNLOADS_FOLDER)
    if video_files:
        upload_links = []  # List to store upload links
        for video_file in video_files:
            file_path = os.path.join(DOWNLOADS_FOLDER, video_file)
            upload_link = upload_file(file_path)
            if upload_link:
                upload_links.append(upload_link)  # Collect the upload link
        if upload_links:
            # Send message with all upload links after completion
            send_telegram_message("Upload completed successfully. Here are the download links:\n" + "\n".join(upload_links))
    else:
        print("No video files found to upload.")

if __name__ == "__main__":
    main()