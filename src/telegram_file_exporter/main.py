import argparse
import json
import random
import time
import os
from datetime import datetime
from telethon import TelegramClient
from telethon.tl.types import MessageMediaDocument
from telethon.utils import get_display_name

# Define allowed extensions and size limit
ALLOWED_EXTENSIONS = {
    ".zip",
    ".tar",
    ".gz",
    ".7z",
    ".rar",
    ".xls",
    ".xlsx",
    ".csv",
    ".txt",
    ".doc",
    ".docx",
}
DEFAULT_SIZE_LIMIT_MB = 3 * 1024


async def export_documents(
    api_id,
    api_hash,
    channel_name,
    output_file,
    max_limit,
    mode,
    output,
    download_dir=None,
    size_limit_mb=DEFAULT_SIZE_LIMIT_MB,
):
    print("Initializing Telegram client...")
    async with TelegramClient("session_name", api_id, api_hash) as client:
        print("Client initialized. Getting channel entity...")
        try:
            channel = await client.get_entity(channel_name)
            channel_display_name = get_display_name(channel)
            print(f"Channel found: {channel_display_name}")

            if mode == "download" and output:
                if not download_dir:
                    download_dir = os.getcwd()
                output_file = os.path.join(download_dir, output_file)

            files_downloaded = 0
            files_existed = 0
            messages_processed = 0

            channel_data = []

            print("Fetching messages...")
            async for message in client.iter_messages(channel, limit=max_limit):
                messages_processed += 1

                if message.media and isinstance(message.media, MessageMediaDocument):
                    try:
                        file_name = None
                        for attr in message.media.document.attributes:
                            if hasattr(attr, "file_name"):
                                file_name = attr.file_name.strip("")
                                break

                        if file_name is None:
                            print("No valid file name found in this message.")
                            raise AttributeError("Document has no valid file_name")

                        # Check if the file extension is allowed
                        file_ext = os.path.splitext(file_name)[-1].lower()
                        if file_ext not in ALLOWED_EXTENSIONS:
                            print(f"File {file_name} skipped (extension not allowed).")
                            continue

                        file_id = message.media.document.id
                        file_size_mb = message.media.document.size / (1024 * 1024)
                        if file_size_mb > size_limit_mb:
                            print(f"{file_name} size {file_size_mb} MB exceeds limit")
                            continue

                        date_posted = message.date.strftime("%Y-%m-%d %H:%M:%S")
                        date_posted_yyyymmdd = message.date.strftime("%Y%m%d")
                        combined_name = f"{date_posted_yyyymmdd}-{file_name}"

                        # Generate the post URL
                        if hasattr(channel, "username") and channel.username:
                            post_url = f"https://t.me/{channel.username}/{message.id}"
                        else:
                            channel_id = abs(
                                channel.id
                            )  # Convert to positive if it"s negative
                            post_url = f"https://t.me/c/{channel_id}/{message.id}"

                        print(f"Processing: {combined_name}, Post URL: {post_url}")

                        # Check if file already exists
                        file_exists = False
                        if mode == "download":
                            file_path = os.path.join(download_dir, combined_name)
                            if os.path.exists(file_path):
                                print(f"File already exists: {file_path}")
                                file_exists = True
                                files_existed += 1

                        message_data = {
                            "File Name": file_name,
                            "File ID": file_id,
                            "Date Posted": date_posted,
                            "Combined Name": combined_name,
                            "Post URL": post_url,
                        }
                        channel_data.append(message_data)

                        if mode == "download" and not file_exists:
                            print(f"Downloading file to: {file_path}")
                            await client.download_media(message.media, file_path)
                            files_downloaded += 1

                    except Exception as e:
                        print(f"An error occurred while processing a message: {e}")
                        continue

                else:
                    print("No file attached to this message.")
                    message_data = {
                        "File Name": "No file attached",
                        "File ID": "",
                        "Date Posted": message.date.strftime("%Y-%m-%d %H:%M:%S"),
                        "Combined Name": "No file attached",
                        "Post URL": (
                            f"https://t.me/c/{abs(channel.id)}/{message.id}"
                            if not channel.username
                            else f"https://t.me/{channel.username}/{message.id}"
                        ),
                    }
                    channel_data.append(message_data)

                # Jittering: random delay between 1 to 3 seconds
                delay = random.uniform(1, 3)
                time.sleep(delay)

                if messages_processed >= max_limit:
                    break

            if output:
                output_data = {channel_display_name: channel_data}
                with open(output_file, "w", encoding="utf8") as jsonfile:
                    json.dump(output_data, jsonfile, indent=4)

                print(f"Export completed. Data stored in {output_file}.")
                print(f"Files downloaded/existed: {files_downloaded}/{files_existed}.")

        except Exception as e:
            print(f"An error occurred: {e}")


def cli():
    parser = argparse.ArgumentParser(
        description="Export list of document files from a Telegram channel."
    )
    parser.add_argument(
        "--api-id",
        type=str,
        help="Telegram API ID",
    )
    parser.add_argument(
        "--api-hash",
        type=str,
        help="Telegram API Hash",
    )
    parser.add_argument(
        "-c",
        "--channel",
        type=str,
        help="Channel username or ID",
    )
    parser.add_argument(
        "-o",
        "--output",
        action="store_true",
        help="Boolean flag to output JSON file. Defaults to True.",
        default=True,
    )
    parser.add_argument(
        "-m",
        "--max",
        type=int,
        default=100,
        help="Max number of channel messages to process.",
    )
    parser.add_argument(
        "--mode",
        choices=["list", "download"],
        default="list",
        help="Mode of operation: 'list' to list files, 'download' to download files.",
    )
    parser.add_argument(
        "--download-dir",
        type=str,
        help="Directory to download files to. Defaults to current directory.",
    )
    parser.add_argument(
        "--size-limit",
        type=int,
        default=DEFAULT_SIZE_LIMIT_MB,
        help="Size limit for downloadable files in megabytes.",
    )

    args = parser.parse_args()
    return args


def main():
    cli_args = cli()

    # Create a timestamp for the output file
    if cli_args.output:
        timestamp = datetime.now().strftime("%Y%m%d")
        channel_name_sanitized = cli_args.c
        print(timestamp, channel_name_sanitized)
