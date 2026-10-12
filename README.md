# ID Tool

This is an ID number generation/verification tool for learning, demonstration, and testing, including: 
- Interactive menu
- Command-line mode
- 17-bit check bit calculation
- 14-bit basic information exhaustive
- Controllable batch generation (limited/unlimited)

Important note
- For study, testing, demonstration, and simulation purposes only
- Strictly prohibited from any illegal use, identity fraud, privacy violations, or violations of local laws and regulations
- Do not submit real personal information, real ID numbers, or real area code data into the warehouse

## How to use

### 1. Interactive operation
```bash
python id_tool.py
```

### 2. Generate samples
```bash
python id_tool.py generate --count 10 --output results.csv
```

### 3. Unlimited generation (use with caution)
```bash
python id_tool.py generate --infinite --output output/id_stream.csv
```

### 4. Calculate the 17-bit check code
```bash
python id_tool.py calc17 11000020000101123
```

### 5. 14 Exhaustive Listings
```bash
python id_tool.py exhaust14 11000020000101 --filter male
```

## Document Description
- 'id_tool.py': Main script
- 'README.md': Project description
- 'LICENSE': MIT license
- '.gitignore': Ignores development and output files

## Safety Recommendations
- Keep the warehouse private or share it only with trusted users
- Do not store real ID card data in the warehouse
- If you need a real area code, please provide it yourself and comply with local laws and regulations
- Always confirm permissions and compliance before using in any public setting

## Chinese and English versions of the prompt

To use the Chinese version of ID-Tool, please go to https://github.com/asdasd5543/id-tool/releases/tag/v1.0.0

To use the English version of the ID-Tool, please visit https://github.com/asdasd5543/English-version-ID-Tool/releases/tag/v1.0.0
