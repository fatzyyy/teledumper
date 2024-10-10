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


def cli():
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
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
        default=[ext.lower() for ext in DEFAULT_ALLOWED_EXTENSIONS],
        help="Allowed file extensions (case insensitive).",
    )

    return parser.parse_args()


def sanitize_filename(message, file_name):
    """
    Sanitize and create a combined filename for downloaded files.

    Args:
        message (telethon.tl.custom.message.Message): The message containing the file.
        file_name (str): The original file name.

    Returns:
        str: The sanitized and combined file name.
    """
    date_posted_yyyymmdd = message.date.strftime("%Y%m%d")
    return f"{date_posted_yyyymmdd}-{file_name}"


def get_post_url(channel, message):
    """
    Generate a post URL based on the channel type.

    Args:
        channel (telethon.tl.custom.channel.Channel): The Telegram channel.
        message (telethon.tl.custom.message.Message): The Telegram message.

    Returns:
        str: The URL to the message.
    """
    if hasattr(channel, "username") and channel.username:
        return f"https://t.me/{channel.username}/{message.id}"
    else:
        channel_id = abs(channel.id)  # Convert to positive if negative
        return f"https://t.me/c/{channel_id}/{message.id}"


async def process_message(
    client, message, channel, allowed_extensions, size_limit_mb, download_dir, mode
):
    """
    Process each message to extract and possibly download multiple files.

    Args:
        client (telethon.client.telegramclient.TelegramClient): The Telegram client.
        message (telethon.tl.custom.message.Message): The message to process.
        channel (telethon.tl.custom.channel.Channel): The Telegram channel.
        allowed_extensions (set): Set of allowed file extensions.
        size_limit_mb (int): Maximum file size allowed in MB.
        download_dir (str): Directory to download files to.
        mode (str): Mode of operation ('list' or 'download').

    Returns:
        list[dict]: A list of processed file data.
    """
    msg_id = message.id
    print(f"Processing message ID: {msg_id}")

    if not message.media or not isinstance(message.media, MessageMediaDocument):
        print(f"No media found in message ID: {msg_id}")
        return []

    # Process all files (in case there are multiple documents)
    files_data = []
    media = (
        message.media if isinstance(message.media, list) else [message.media]
    )  # Support multiple attachments

    for doc in media:
        file_name = next(
            (
                attr.file_name.strip()
                for attr in doc.document.attributes
                if hasattr(attr, "file_name")
            ),
            None,
        )
        if not file_name:
            print(f"File name missing in message ID: {msg_id}")
            continue

        # Check file extension
        file_ext = os.path.splitext(file_name)[-1].lower()
        if file_ext not in (ext.lower() for ext in allowed_extensions):
            print(f"{file_name} extension {file_ext} not allowed")
            continue  # Skip file if the extension is not allowed

        # Check file size
        file_size_mb = doc.document.size / (1024 * 1024)
        if file_size_mb > size_limit_mb:
            print(f"Skipping {file_name} size {file_size_mb} MB exceeds limit")
            continue  # Skip file if it exceeds the size limit

        combined_name = sanitize_filename(message, file_name)
        post_url = get_post_url(channel, message)

        file_exists = False
        file_path = None
        if mode == "download":
            file_path = os.path.join(download_dir, combined_name)
            if os.path.exists(file_path):
                print(f"File {file_name} already exists at {file_path}")
                file_exists = True

        print(f"File {file_name} ready to be processed/downloaded")

        file_data = {
            "file_name": file_name,
            "file_path": file_path,
            "post_url": post_url,
            "file_exists": file_exists,
            "file_size_mb": file_size_mb,
        }
        files_data.append(file_data)

    return files_data


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
    """
    Main function to export or download documents.

    Args:
        api_id (str): Telegram API ID.
        api_hash (str): Telegram API hash.
        channel_name (str): Telegram channel name or ID.
        output_file (str): File to store the exported data.
        max_limit (int): Max number of messages to process.
        mode (str): Mode of operation ('list' or 'download').
        output (bool): Whether to output a JSON file.
        download_dir (str): Directory to download files to.
        size_limit_mb (int): Max file size to download in MB.
        allowed_extensions (set): Set of allowed file extensions.
    """
    allowed_extensions = allowed_extensions or DEFAULT_ALLOWED_EXTENSIONS
    download_dir = download_dir or os.getcwd()

    print(f"Allowed extensions: {allowed_extensions}")
    print(f"Size limit: {size_limit_mb} MB")
    print(f"Mode: {mode}")
    print(f"Download directory: {download_dir}")

    print("Initializing Telegram client...")
    async with TelegramClient("session_name", api_id, api_hash) as client:
        try:
            channel = await client.get_entity(channel_name)
            print(f"Channel found: {get_display_name(channel)}")

            files_downloaded, files_existed, msgs_processed = 0, 0, 0
            channel_data = []

            print(f"Fetching up to {max_limit} messages from {channel_name}...")
            async for message in client.iter_messages(channel, limit=max_limit):
                msgs_processed += 1
                msg_id = message.id
                print(f"Processing message {msgs_processed}/{max_limit} (ID: {msg_id})")
                # Process the message and return a list of files
                files_data = await process_message(
                    client,
                    message,
                    channel,
                    allowed_extensions,
                    size_limit_mb,
                    download_dir,
                    mode,
                )

                for file_data in files_data:
                    file_name = file_data["file_name"]
                    file_url = file_data["post_url"]
                    file_path = file_data["file_path"]

                    message_data = {
                        "File Name": file_name,
                        "Date Posted": message.date.strftime("%Y-%m-%d %H:%M:%S"),
                        "Combined Name": sanitize_filename(message, file_name),
                        "Post URL": file_url,
                    }
                    channel_data.append(message_data)

                    if mode == "download" and not file_data["file_exists"]:
                        print(f"Downloading file {file_name} to {file_path}")
                        await client.download_media(message.media, file_path)
                        files_downloaded += 1
                    elif file_data["file_exists"]:
                        files_existed += 1

                delay = random.uniform(1, 3)
                print(f"Sleeping for {delay:.2f} seconds...")
                time.sleep(delay)

                if msgs_processed >= max_limit:
                    break

            if output:
                print(f"Writing output to {output_file}...")
                with open(output_file, "w") as jsonfile:
                    json.dump(
                        {get_display_name(channel): channel_data}, jsonfile, indent=4
                    )
                print(f"Export completed. Data stored in {output_file}.")

        except Exception as e:
            print(f"An error occurred: {e}")


def main():
    """
    Main entry point for the script.
    """
    args = cli()

    output_filename = None
    if args.output:
        timestamp = datetime.now().strftime("%Y%m%d")
        channel_name_sanitized = args.channel.replace("@", "").replace("/", "_")
        output_filename = f"{timestamp}-{channel_name_sanitized}.json"

    print("Starting the export process...")
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
    print("Export process finished!")


if __name__ == "__main__":
    main()
