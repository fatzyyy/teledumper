import argparse
import asyncio
import csv
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
            channel_display_name = get_display_name(channel)
            print(f"Channel found: {channel_display_name}")

            # If in download mode, set output file in download directory
            if mode == "download" and output:
                if not download_dir:
                    download_dir = os.getcwd()
                output_file = os.path.join(download_dir, output_file)

            files_downloaded = 0
            files_existed = 0
            msgs_processed = 0

            if output:
                with open(output_file, "w", newline="") as csvfile:
                    fieldnames = [
                        "File Name",
                        "File ID",
                        "Date Posted",
                        "Combined Name",
                        "Post URL",
                    ]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()

                    # Iterating through the messages in the channel
                    print("Fetching messages...")
                    async for msg in client.iter_messages(channel, limit=max_limit):
                        msgs_processed += 1

                        if msg.media and isinstance(msg.media, MessageMediaDocument):
                            file_name = msg.media.document.attributes[-1].file_name
                            file_id = msg.media.document.id
                            date_posted = msg.date.strftime("%Y-%m-%d %H:%M:%S")
                            date_posted_yyyymmdd = msg.date.strftime("%Y%m%d")
                            combined_name = f"{date_posted_yyyymmdd}-{file_name}"

                            # Generate the post URL
                            if hasattr(channel, "username") and channel.username:
                                post_url = f"https://t.me/{channel.username}/{msg.id}"
                            else:
                                channel_id = abs(
                                    channel.id
                                )  # Convert to positive if it's negative
                                post_url = f"https://t.me/c/{channel_id}/{msg.id}"

                            print(f"Processing: {combined_name}, Post URL: {post_url}")

                            # Check if file already exists
                            file_exists = False
                            if mode == "download":
                                file_path = os.path.join(download_dir, combined_name)
                                if os.path.exists(file_path):
                                    print(f"File already exists: {file_path}")
                                    file_exists = True
                                    files_existed += 1

                            writer.writerow(
                                {
                                    "File Name": file_name,
                                    "File ID": file_id,
                                    "Date Posted": date_posted,
                                    "Combined Name": combined_name,
                                    "Post URL": post_url,
                                }
                            )

                            if mode == "download" and not file_exists:
                                print(f"Downloading file to: {file_path}")
                                await client.download_media(msg.media, file_path)
                                files_downloaded += 1

                        else:
                            print("No file attached to this msg.")
                            writer.writerow(
                                {
                                    "File Name": "No file attached",
                                    "File ID": "",
                                    "Date Posted": msg.date.strftime(
                                        "%Y-%m-%d %H:%M:%S"
                                    ),
                                    "Combined Name": "No file attached",
                                    "Post URL": (
                                        f"https://t.me/c/{abs(channel.id)}/{msg.id}"
                                        if not channel.username
                                        else f"https://t.me/{channel.username}/{msg.id}"
                                    ),
                                }
                            )

                        # Jittering: random delay between 1 to 3 seconds
                        delay = random.uniform(1, 3)
                        time.sleep(delay)

                        if msgs_processed >= max_limit:
                            break

                print(f"Export completed. Document files listed in {output_file}.")
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
        help="Boolean flag to output CSV file. Defaults to True.",
        default=True,
    )
    parser.add_argument(
        "-m",
        "--max",
        type=int,
        default=100,
        help="Max number of channel msgs to process.",
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
        output_filename = f"{timestamp}-{channel_name_sanitized}.csv"
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
