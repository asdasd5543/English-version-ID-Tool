# ID Tool

ID Tool is a Python command-line and interactive utility for generating synthetic ID-number samples and demonstrating checksum calculations. Use it only for educational, testing, and simulation purposes.

## Features

- Interactive menu and command-line interface
- User-selected batch size, with no hard generation limit
- Optional continuous generation, stopped with `Ctrl+C`
- 18-digit checksum calculation from a 17-digit input
- Exhaustive generation of sequence variants for a 14-digit base
- Sample area codes included by default; custom area-code files require explicit opt-in

## Requirements

- Python 3.8 or later
- No third-party packages are required

## Usage

Run the interactive menu:

```bash
python id-tool-v1.0.1-en.py
```

In the menu, choose batch generation and enter the number of records you want. There is no fixed maximum. Large batches may take longer to generate and use more disk space; the program displays a warning and asks for confirmation.

To generate a specific number of records from the command line:

```bash
python id-tool-v1.0.1-en.py generate --count 10 --output results.csv
```

To generate continuously until interrupted:

```bash
python id-tool-v1.0.1-en.py generate --infinite --output output/id_stream.csv
```

`--confirm` skips the interactive confirmation prompt. Use it only when running the command non-interactively and you have checked the requested operation.

Calculate the checksum digit for a 17-digit value:

```bash
python id-tool-v1.0.1-en.py calc17 11000020000101123
```

Generate sequence variants for a 14-digit base, optionally filtering by gender:

```bash
python id-tool-v1.0.1-en.py exhaust14 11000020000101 --filter male
```

To use your own area-code file, explicitly enable it:

```bash
python id-tool-v1.0.1-en.py generate --count 10 --area-codes-file area_codes.csv --allow-custom-area-codes
```

The custom file can be a CSV file with area codes in its first column or a plain-text file with one code per line.

## Safety and privacy

- Use generated values only as synthetic test data. Do not use them to impersonate real people, bypass identity checks, or create fraudulent documents.
- Do not enter or store real personal information, ID numbers, or sensitive area-code datasets in this repository.
- Obtain any custom data lawfully and follow applicable privacy requirements and local laws.
- Be aware that large or continuous runs can consume significant time and storage.

## Project files

- `id-tool-v1.0.1-en.py`: main script
- `README.md`: project documentation
- `LICENSE`: MIT license

## Chinese and English versions

- Chinese version: https://github.com/asdasd5543/id-tool/releases/tag/v1.0.0
- English version: https://github.com/asdasd5543/English-version-ID-Tool/releases/tag/v1.0.1
