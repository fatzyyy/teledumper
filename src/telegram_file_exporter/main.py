"""Main module"""

import argparse
import asyncio
import json
import random
import time
import os
from datetime import datetime
from telethon import TelegramClient
from telethon.tl.types import MessageMediaDocument
from telethon.utils import get_display_name

# Define default allowed extensions and size limit
DEFAULT_ALLOWED_EXTENSIONS = {
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
DEFAULT_SIZE_LIMIT_MB = 3 * 1024  # 3 GB in MB


def parse_args():
    """CLI argument parsing"""
    parser = argparse.ArgumentParser(
        description="Export list of document files from a Telegram channel."
    )
    parser.add_argument("--api-id", type=str, help="Telegram API ID")
    parser.add_argument("--api-hash", type=str, help="Telegram API Hash")
    parser.add_argument("-c", "--channel", type=str, help="Channel username or ID")
    parser.add_argument(
        "-o",
        "--output",
        action="store_true",
        default=True,
        help="Output JSON file (default: True)",
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
        help="Mode: 'list' or 'download'.",
    )
    parser.add_argument(
        "--download-dir",
        type=str,
        help="Directory to download files to (default: current dir).",
    )
    parser.add_argument(
        "--size-limit",
        type=int,
        default=DEFAULT_SIZE_LIMIT_MB,
        help="Size limit in MB (default: 3 GB).",
    )
    parser.add_argument(
        "--extensions",
        type=str,
        nargs="*",
        default=DEFAULT_ALLOWED_EXTENSIONS,
        help="Allowed file extensions.",
    )

    return parser.parse_args()


def sanitize_filename(message, file_name):
    """Sanitize and create a combined filename for downloaded files"""
    date_posted_yyyymmdd = message.date.strftime("%Y%m%d")
    return f"{date_posted_yyyymmdd}-{file_name}"


def get_post_url(channel, message):
    """Generate a post URL based on the channel type"""
    if hasattr(channel, "username") and channel.username:
        return f"https://t.me/{channel.username}/{message.id}"
    else:
        channel_id = abs(channel.id)  # Convert to positive if negative
        return f"https://t.me/c/{channel_id}/{message.id}"


async def process_message(
    client, message, channel, allowed_extensions, size_limit_mb, download_dir, mode
):
    """Process each message to extract and possibly download files"""
    if not message.media or not isinstance(message.media, MessageMediaDocument):
        return None, None, None, None  # Return 4 values even if some are None

    file_name = next(
        (
            attr.file_name.strip()
            for attr in message.media.document.attributes
            if hasattr(attr, "file_name")
        ),
        None,
    )
    if not file_name:
        return None, None, None, None  # Return 4 values even if some are None

    # Check file extension
    file_ext = os.path.splitext(file_name)[-1].lower()
    if file_ext not in allowed_extensions:
        return None, None, None, None  # Skip if extension not allowed

    # Check file size
    file_size_mb = message.media.document.size / (1024 * 1024)
    if file_size_mb > size_limit_mb:
        return None, None, None, None  # Skip if size exceeds limit

    combined_name = sanitize_filename(message, file_name)
    post_url = get_post_url(channel, message)

    file_exists = False
    file_path = None
    if mode == "download":
        file_path = os.path.join(download_dir, combined_name)
        if os.path.exists(file_path):
            file_exists = True

    return file_name, file_path, post_url, file_exists


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
    allowed_extensions=None,
):
    """Main function to export or download documents"""
    allowed_extensions = allowed_extensions or DEFAULT_ALLOWED_EXTENSIONS
    download_dir = download_dir or os.getcwd()

    print("Initializing Telegram client...")
    async with TelegramClient("session_name", api_id, api_hash) as client:
        try:
            channel = await client.get_entity(channel_name)
            print(f"Channel found: {get_display_name(channel)}")

            files_downloaded, files_existed, messages_processed = 0, 0, 0
            channel_data = []

            async for message in client.iter_messages(channel, limit=max_limit):
                messages_processed += 1

                file_name, file_path, post_url, file_exists = await process_message(
                    client,
                    message,
                    channel,
                    allowed_extensions,
                    size_limit_mb,
                    download_dir,
                    mode,
                )

                if file_name:
                    message_data = {
                        "File Name": file_name,
                        "File ID": message.media.document.id,
                        "Date Posted": message.date.strftime("%Y-%m-%d %H:%M:%S"),
                        "Combined Name": sanitize_filename(message, file_name),
                        "Post URL": post_url,
                    }
                    channel_data.append(message_data)

                    if mode == "download" and not file_exists:
                        print(f"Downloading file to: {file_path}")
                        await client.download_media(message.media, file_path)
                        files_downloaded += 1
                    elif file_exists:
                        files_existed += 1

                delay = random.uniform(1, 3)
                time.sleep(delay)

                if messages_processed >= max_limit:
                    break

            if output:
                with open(output_file, "w", encoding="utf-8") as jsonfile:
                    json.dump(
                        {get_display_name(channel): channel_data}, jsonfile, indent=4
                    )
                print(f"Export completed. Data stored in {output_file}")

        except Exception as e:
            print(f"An error occurred: {e}")


def main():
    """Main function"""
    args = parse_args()

    output_filename = None
    if args.output:
        timestamp = datetime.now().strftime("%Y%m%d")
        channel_name_sanitized = args.channel.replace("@", "").replace("/", "_")
        output_filename = f"{timestamp}-{channel_name_sanitized}.json"

    asyncio.run(
        export_documents(
            args.api_id,
            args.api_hash,
            args.channel,
            output_filename,
            args.max,
            args.mode,
            args.output,
            args.download_dir,
            args.size_limit,
            args.extensions,
        )
    )


if __name__ == "__main__":
    main()
