ID Tool
This is an ID number generation/validation tool for learning, demonstration, and testing purposes. It includes:
- Interactive menu
- Command-line mode
- 17-digit checksum calculation
- 14-digit basic information enumeration
- Controlled batch generation (limited/unlimited)
Important Notice
- This project is only for learning, testing, demonstration, and simulation purposes.
- Strictly prohibited for any illegal use, identity fraud, privacy violations, or activities that violate local laws and regulations.
- Do not submit real personal information, real ID numbers, or real area code data to this repository.
Usage
1. Interactive Mode
python id_tool.py
2. Generate Examples
python id_tool.py generate --count 10 --output results.csv
3. Unlimited Generation (Use with Caution)
python id_tool.py generate --infinite --output output/id_stream.csv
4. Calculate 17-Digit Checksum
python id_tool.py calc17 11000020000101123
5. 14-Digit Enumeration
python id_tool.py exhaust14 11000020000101 --filter male
File Description
- id_tool.py: Main script
- README.md: Project documentation
- LICENSE: MIT License
- .gitignore: Ignores development files and output files
Safety Recommendations
- Keep the repository private or share it only with trusted users.
- Do not store real identity data in the repository.
- If real area codes are required, provide them yourself and comply with local laws and regulations.
- Before using this project in any public environment, make sure permissions and compliance requirements are confirmed.
