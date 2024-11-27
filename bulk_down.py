import os
import subprocess
import requests
import time

# Configuration
DOWNLOADS_FOLDER = os.path.expanduser("./Downloads")
ARIA2_PATH = "aria2c"  # Ensure 'aria2c' is in your PATH
LINKS_FILE = "links.txt"  # File containing URLs to download
ZIP_ENABLED = True  # Set this to True or False based on your requirement
ZIP_FILE_NAME = "Gangnam.B-Side.1080p.DSNP.WEB-DL.DDP5.1.H.264"  # Custom name for the zip file

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

def download_files_with_aria2(urls):
    """ Download multiple files using aria2. """
    ensure_directory_exists(DOWNLOADS_FOLDER)

    aria2_file = os.path.join(DOWNLOADS_FOLDER, "aria2_downloads.txt")

    with open(aria2_file, 'w') as f:
        for url in urls:
            f.write(url + '\n')

    send_telegram_message("Download started for the following files:\n" + "\n".join(urls))

    command = [ARIA2_PATH, '-i', aria2_file, '--dir', DOWNLOADS_FOLDER, '--continue', '-x16']
    try:
        subprocess.run(command, check=True)
        print("All downloads initiated.")
        send_telegram_message("Download completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error downloading files: {e}")
        send_telegram_message("Error occurred during download.")

    return aria2_file

def read_urls_from_file(file_path):
    """ Read URLs from a text file. """
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def get_video_files(folder):
    """ Get a list of video files in the given folder. """
    video_extensions = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.mpeg', '.mpg')
    return [f for f in os.listdir(folder) if f.endswith(video_extensions)]

def zip_files(file_paths, zip_name):
    """ Zips the provided file paths into a single zip file using p7zip. """
    print(f"Zipping files: {file_paths} into {zip_name}")
    send_telegram_message("Started Zipping Files...")  # Notify that zipping has started

    start_time = time.time()  # Capture the start time
    command = ['7z', 'a', '-mx0', zip_name] + file_paths
    try:
        subprocess.run(command, check=True)
        elapsed_time = time.time() - start_time  # Calculate elapsed time
        print(f"Successfully created zip file: {zip_name}")
        print(f"Elapsed time for zipping: {elapsed_time:.2f} seconds")

        # Send a message with the elapsed time to Telegram
        send_telegram_message(f"Zipping completed successfully in {elapsed_time:.2f} seconds.")
    except subprocess.CalledProcessError as e:
        print(f"Error creating zip file: {e}")

def main():
    """ Main function to handle downloading. """
    urls_to_download = read_urls_from_file(LINKS_FILE)

    existing_files = {url.split("/")[-1]: os.path.join(DOWNLOADS_FOLDER, url.split("/")[-1])
                      for url in urls_to_download if os.path.exists(os.path.join(DOWNLOADS_FOLDER, url.split("/")[-1]))}

    urls_to_download = [url for url in urls_to_download if url.split("/")[-1] not in existing_files]

    if urls_to_download:
        download_files_with_aria2(urls_to_download)
        print("Download completed successfully.")
    else:
        print("All files already exist, no new downloads initiated.")

    # Process video files for zipping if ZIP_ENABLED is set to True
    video_files = get_video_files(DOWNLOADS_FOLDER)
    if video_files and ZIP_ENABLED:
        zip_name = os.path.join(DOWNLOADS_FOLDER, ZIP_FILE_NAME + '.7z')  # Custom zip file name with default extension
        zip_files([os.path.join(DOWNLOADS_FOLDER, f) for f in video_files], zip_name)

        # Remove original files after zipping
        for video_file in video_files:
            os.remove(os.path.join(DOWNLOADS_FOLDER, video_file))
    elif not ZIP_ENABLED:
        print("Zipping is disabled. Skipping zipping step.")

if __name__ == "__main__":
    main()
