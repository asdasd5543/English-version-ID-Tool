# ID Tool

This project is a synthetic ID number generator and validator for learning, demonstration, and testing. It includes:
- An interactive menu
- Command-line mode
- 17-digit checksum calculation
- Exhaustive 14-digit base-number generation
- Controlled batch generation (limited or infinite)

Important notice
- Intended for study, testing, demonstration, and simulation only
- Strictly prohibited: illegal use, identity fraud, privacy violations, or any violation of local laws and regulations
- Do not submit real personal information, real ID numbers, or real area-code data to this repository

## Usage

### 1. Interactive mode
```bash
python id-tool-v1.0.0-en.py
```

### 2. Generate sample IDs
```bash
python id-tool-v1.0.0-en.py generate --count 10 --output results.csv
```

### 3. Infinite generation (use with caution)
```bash
python id-tool-v1.0.0-en.py generate --infinite --output output/id_stream.csv --confirm
```

### 4. Calculate the 17-digit checksum
```bash
python id-tool-v1.0.0-en.py calc17 11000020000101123
```

### 5. Exhaustive 14-digit search
```bash
python id-tool-v1.0.0-en.py exhaust14 11000020000101 --filter male
```

## Project files
- `id-tool-v1.0.0-en.py`: main script
- `README.md`: project documentation
- `LICENSE`: MIT license
- `.gitignore`: ignores local development and output files

## Safety recommendations
- Keep this repository private or share it only with trusted users
- Do not store real ID-card data in the repository
- If you need real area codes, obtain them legally and only in compliance with local laws and regulations
- Always verify permissions and compliance before using the tool in public or shared environments

## Chinese and English versions

To use the Chinese version of ID Tool, visit: https://github.com/asdasd5543/id-tool/releases/tag/v1.0.0

To use the English version of ID Tool, visit: https://github.com/asdasd5543/English-version-ID-Tool/releases/tag/v1.0.0
