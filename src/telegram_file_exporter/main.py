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


async def export_documents(
    api_id,
    api_hash,
    channel_name,
    output_file,
    max_limit,
    mode,
    output,
    download_dir=None,
):
    print("Initializing Telegram client...")
    async with TelegramClient("session_name", api_id, api_hash) as client:
        print("Client initialized. Getting channel entity...")
        try:
            channel = await client.get_entity(channel_name)
            channel_name = channel.username
            channel_display = get_display_name(channel)
            print(f"Channel found: {channel_name}/{channel_display}")

            # If in download mode, set output file in download directory
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
                    file_name = message.media.document.attributes[-1].file_name
                    file_id = message.media.document.id
                    date_posted = message.date.strftime("%Y-%m-%d %H:%M:%S")
                    date_posted_yyyymmdd = message.date.strftime("%Y%m%d")
                    combined_name = f"{date_posted_yyyymmdd}-{file_name}"

                    # Generate the post URL
                    if hasattr(channel, "username") and channel_name:
                        post_url = f"https://t.me/{channel_name}/{message.id}"
                    else:
                        channel_id = abs(
                            channel.id
                        )  # Convert to positive if it's negative
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
                output_data = {channel_display: channel_data}
                with open(output_file, "w") as jsonfile:
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

    args = parser.parse_args()
    return args


def main():
    cli_args = cli()

    # Create a timestamp for the output file
    if cli_args.output:
        timestamp = datetime.now().strftime("%Y%m%d")
        channel_name_sanitized = cli_args.channel.replace("@", "").replace("/", "_")
        output_filename = f"{timestamp}-{channel_name_sanitized}.json"
    else:
        output_filename = None

    asyncio.run(
        export_documents(
            cli_args.api_id,
            cli_args.api_hash,
            cli_args.channel,
            output_filename,
            cli_args.max,
            cli_args.mode,
            cli_args.output,
            cli_args.download_dir,
        )
    )


if __name__ == "__main__":
    main()
