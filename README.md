# Teledumper

Teledumper is a specialized, OSINT-talored tool for exporting messages and files from Telegram channels.

## Features

- Export document files from a Telegram channel.
- Optionally download the files to a specified directory.
- Output the list of files and their metadata to a JSON file.
- Supports processing a specified number of messages from a channel.

## Installation

First, clone the repository:

```bash
git clone https://github.com/yourusername/teledumper.git
cd telegram-file-exporter
pip install .
```

## Usage

```bash
telegram-file-exporter --api-id <your_api_id> --api-hash <your_api_hash> --channel <channel_name_or_id> --mode <list|download> [options]
```

### Arguments

- --api-id: Your Telegram API ID.
- --api-hash: Your Telegram API Hash.
- --channel: The username or ID of the Telegram channel.
- --mode: The mode of operation. Use list to list files, or download to download files.
- --output: Boolean flag to output a JSON file (default: True).
- --max: Maximum number of messages to process from the channel (default: 100).
- --download-dir: Directory to download files to (default: current directory).

### Examples

```bash
# List Files in a Channel
teledumper --api-id 12345 --api-hash abcdef --channel @mychannel --mode list -m 100

# Download Files from a Channel
teledumper --api-id 12345 --api-hash abcdef --channel @mychannel --mode download --download-dir ./downloads -m 100
```

## Requirements

See [Pipfile](./Pipfile)

## Credits

This project was created and is maintained by Leonid Akinin <fatzy@protonmail.com>. If you use or fork this project, please provide proper credit and a link back to the original repository.

## License

See [License](./LICENSE)
