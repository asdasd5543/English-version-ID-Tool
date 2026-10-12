#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive + CLI hybrid: ID number sequence generator and validation tool (with infinite mode)
- Press Ctrl+C during generation: stop current generation and return to the main menu (without exiting)
- Both interactive mode and CLI support infinite generation (enter inf or use --infinite)
Disclaimer: For educational/testing/simulation purposes only. Illegal use is strictly prohibited.
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

# Checksum calculation constants
_WEIGHTS = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
_MAPPING = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']


class UserInterruptedToMenu(Exception):
    """Signal used to catch Ctrl+C during generation and return to the interactive menu"""
    def __init__(self, generated: int = 0):
        self.generated = generated
        super().__init__("User interrupted, returning to menu")


def get_system_location_info() -> Tuple[datetime, str, str]:
    local_now = datetime.now().astimezone()
    tz_name = "Local Time"
    offset = local_now.utcoffset()
    utc_offset_hours = (offset.total_seconds() / 3600.0) if offset else 0.0
    offset_str = f"UTC{utc_offset_hours:+.1f}"
    return local_now, tz_name, offset_str


def calculate_check_digit(num_str: str) -> str:
    if len(num_str) != 17 or not num_str.isdigit():
        raise ValueError("calculate_check_digit: Input must be a 17-digit numeric string")
    total = sum(int(num_str[i]) * _WEIGHTS[i] for i in range(17))
    return _MAPPING[total % 11]


def load_area_codes_from_file(path: Path) -> List[str]:
    codes: List[str] = []
    if not path.exists():
        raise FileNotFoundError(f"Area code file does not exist: {path}")
    with path.open(encoding="utf-8") as f:
        try:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                code = row[0].strip()
                if code and code.isdigit():
                    codes.append(code)
        except Exception:
            f.seek(0)
            for line in f:
                code = line.strip()
                if code and code.isdigit():
                    codes.append(code)
    return codes


# Default example area codes: only a few samples are used to avoid disclosure or misuse
_DEFAULT_AREA_CODES = ['110000', '120000', '310000', '440000', '500000']


def random_id_sequence(
    area_codes: Iterable[str],
    start_date: datetime,
    end_date: datetime,
    count: Optional[int],
) -> Iterable[Tuple[str, str, str]]:
    """
    Generate ID number sequences.
    - If count is None, generate infinitely (continuous yield)
    - Each result is (full_id, birthday_friendly, area_code)
    """
    if start_date >= end_date:
        raise ValueError("Start date must be earlier than end date")
    delta_days = (end_date - start_date).days
    if delta_days <= 0:
        raise ValueError("Date range must be at least one day")

    area_list = list(area_codes)
    if not area_list:
        raise ValueError("No area codes provided")

    if count is None:
        # Infinite mode
        while True:
            area = random.choice(area_list)
            random_days = random.randint(0, delta_days - 1)
            target_date = start_date + timedelta(days=random_days)
            birthday_str = target_date.strftime("%Y%m%d")
            friendly_birthday = target_date.strftime("%Y-%m-%d")
            sequence_num = str(random.randint(0, 999)).zfill(3)
            front_17 = f"{area}{birthday_str}{sequence_num}"
            check_char = calculate_check_digit(front_17)
            full_id = front_17 + check_char
            yield full_id, friendly_birthday, area
    else:
        for _ in range(count):
            area = random.choice(area_list)
            random_days = random.randint(0, delta_days - 1)
            target_date = start_date + timedelta(days=random_days)
            birthday_str = target_date.strftime("%Y%m%d")
            friendly_birthday = target_date.strftime("%Y-%m-%d")
            sequence_num = str(random.randint(0, 999)).zfill(3)
            front_17 = f"{area}{birthday_str}{sequence_num}"
            check_char = calculate_check_digit(front_17)
            full_id = front_17 + check_char
            yield full_id, friendly_birthday, area


def cmd_generate(args: argparse.Namespace) -> int:
    """
    Generate ID number samples in batches.
    - When args.infinite is True, generation continues until Ctrl+C is pressed and requires explicit confirmation.
    - When output is directed to a file, infinite mode writes incrementally to avoid loading everything in memory.
    - User interruptions are converted into a return to the interactive menu instead of exiting the program.
    """
    is_infinite = bool(getattr(args, "infinite", False))
    count_value = int(getattr(args, "count", 10))

    if is_infinite or not getattr(args, "confirm", False):
        print("Warning: generating ID numbers may be sensitive and is intended only for academic, testing, or simulation use.")
        if count_value > 1000:
            print(f"You requested {count_value} records. Large batches should be used only with explicit intent.")
        if not getattr(args, "confirm", False):
            try:
                ans = input("Continue? Enter 'y' to confirm: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print("\nCancelled.")
                return 1
            if ans != 'y':
                print("Cancelled.")
                return 1

    if getattr(args, "area_codes_file", None):
        if not getattr(args, "allow_custom_area_codes", False):
            print("Custom area-code files are disabled by default. Re-run with --allow-custom-area-codes only if you explicitly intend to use a custom source.")
            return 1
        try:
            area_codes = load_area_codes_from_file(Path(args.area_codes_file))
            if not area_codes:
                print("No area codes were loaded from the supplied file. Exiting.")
                return 1
        except Exception as e:
            print(f"Failed to load the custom area-code file: {e}")
            return 1
    else:
        area_codes = _DEFAULT_AREA_CODES

    try:
        start_date = datetime.strptime(getattr(args, "start", "2000-01-01"), "%Y-%m-%d")
        end_date = datetime.strptime(getattr(args, "end", "2020-01-01"), "%Y-%m-%d")
    except ValueError as e:
        print(f"Invalid date format: {e}")
        return 1

    count_param: Optional[int] = None if is_infinite else count_value

    generated = 0

    # If output is directed to a file in infinite mode, write incrementally to avoid loading the full stream in memory.
    outfile = None
    if getattr(args, "output", None):
        out_path = Path(args.output)
        try:
            outfile = out_path.open("w", encoding="utf-8")
        except Exception as e:
            print(f"Cannot open output file: {e}")
            return 1

    try:
        seq_iter = random_id_sequence(area_codes, start_date, end_date, count_param)
        for full_id, birthday, area in seq_iter:
            generated += 1
            line = f"[{generated}] {full_id}  ->  {birthday} (area:{area})"
            print(line)
            if outfile:
                outfile.write(f"{full_id},{birthday},{area}\n")
                if is_infinite:
                    outfile.flush()
    except KeyboardInterrupt:
        # Catch Ctrl+C and return to the main menu without exiting the program.
        if outfile:
            try:
                outfile.flush()
            except Exception:
                pass
        print(f"\n[!] Interrupted by user. Generated {generated} records. Returning to the main menu...")
        raise UserInterruptedToMenu(generated)
    except Exception as e:
        print(f"\nError during generation: {e}")
        if outfile:
            outfile.close()
        return 1
    finally:
        if outfile:
            outfile.close()

    if not is_infinite:
        print(f"Completed: generated {generated} records (range: {getattr(args, 'start', '2000-01-01')} to {getattr(args, 'end', '2020-01-01')}).")
    else:
        print(f"Infinite mode stopped normally: generated {generated} records in total.")
    return 0


def cmd_calc17(args: argparse.Namespace) -> int:
    s = args.value.strip()
    if len(s) != 17 or not s.isdigit():
        print("Error: please enter exactly 17 digits.")
        return 1
    try:
        check_char = calculate_check_digit(s)
    except ValueError as e:
        print(f"Checksum calculation error: {e}")
        return 1

    year = s[6:10]
    month = s[10:12]
    day = s[12:14]
    gender_digit = int(s[-1])
    gender_symbol = "Male" if gender_digit % 2 != 0 else "Female"

    print("-" * 50)
    print(f"Birthday: {year}-{month}-{day}")
    print(f"Gender: {gender_symbol}")
    print(f"18th digit checksum: {check_char}")
    print(f"Full sequence: {s}{check_char}")
    print("-" * 50)
    return 0


def cmd_exhaust14(args: argparse.Namespace) -> int:
    base = args.value.strip()
    if len(base) != 14 or not base.isdigit():
        print("Error: Please enter exactly 14 digits.")
        return 1

    filter_choice = args.filter.lower()
    if filter_choice not in ('male', 'female', 'all'):
        print("Invalid filter. Choose male / female / all")
        return 1

    print(f"Preparing exhaustive search for base {base} (up to 1000 sequence numbers), filter: {filter_choice}")
    if not getattr(args, "confirm", False):
        try:
            ans = input("Continue? Enter y to confirm: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            return 1
        if ans != 'y':
            print("Cancelled.")
            return 1

    results = []
    count = 0
    try:
        for i in range(1000):
            seq_str = str(i).zfill(3)
            gender_digit = int(seq_str[-1])
            is_male = (gender_digit % 2 != 0)

            if filter_choice == 'male' and not is_male:
                continue
            if filter_choice == 'female' and is_male:
                continue

            front_17 = base + seq_str
            check_character = calculate_check_digit(front_17)
            gender_symbol = "Male" if is_male else "Female"
            count += 1
            line = f"[{count}][{seq_str}] {front_17}{check_character} | {gender_symbol}"
            print(line)
            results.append((front_17 + check_character, gender_symbol))
    except KeyboardInterrupt:
        print("\n[⚠️] Exhaustive search interrupted by user.")

    if getattr(args, "output", None):
        try:
            p = Path(args.output)
            with p.open("w", encoding="utf-8") as f:
                for fullid, gender in results:
                    f.write(f"{fullid},{gender}\n")
            print(f"Results written to: {p}")
        except Exception as e:
            print(f"Failed to write file: {e}")
            return 1

    print(f"Completed: output {count} matching records.")
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Synthetic ID number generator and validator (restricted, safe defaults)",
        epilog="Disclaimer: For educational, testing, and simulation use only. Illegal use is strictly prohibited.",
    )
    p.add_argument("--version", action="version", version="id-tool 1.3")
    sub = p.add_subparsers(dest="cmd")

    gen = sub.add_parser("generate", help="Generate synthetic ID samples under safe defaults")
    gen.add_argument("--count", type=int, default=10, help="Number of records to generate (default 10; --infinite takes priority)")
    gen.add_argument("--infinite", action="store_true", help="Generate indefinitely until interrupted (requires explicit confirmation)")
    gen.add_argument("--start", default="2000-01-01", help="Start date (YYYY-MM-DD), default 2000-01-01")
    gen.add_argument("--end", default="2020-01-01", help="End date (YYYY-MM-DD), default 2020-01-01 (exclusive)")
    gen.add_argument("--area-codes-file", default=None, help="Custom area-code file path (CSV or one code per line)")
    gen.add_argument("--allow-custom-area-codes", action="store_true", help="Explicitly allow loading a custom area-code file")
    gen.add_argument("--output", default=None, help="Optional output file path (CSV format)")
    gen.add_argument("--confirm", action="store_true", help="Skip interactive confirmation")
    gen.set_defaults(func=cmd_generate)

    c17 = sub.add_parser("calc17", help="Calculate the 18th checksum digit and parse the birthday and gender")
    c17.add_argument("value", help="17-digit number")
    c17.set_defaults(func=cmd_calc17)

    ex = sub.add_parser("exhaust14", help="Exhaust 000-999 sequence variants for a 14-digit base (optional gender filtering)")
    ex.add_argument("value", help="14-digit base number")
    ex.add_argument("--filter", default="all", help="Filter: male / female / all (default all)")
    ex.add_argument("--output", default=None, help="Optional output file path (CSV)")
    ex.add_argument("--confirm", action="store_true", help="Skip interactive confirmation")
    ex.set_defaults(func=cmd_exhaust14)

    return p


def interactive_mode() -> int:
    """
    Interactive menu used when the user launches the script without CLI arguments.
    Handles UserInterruptedToMenu so Ctrl+C returns to the menu instead of exiting the program.
    """
    while True:
        local_now, tz_name, offset_str = get_system_location_info()
        print("\n" + "=" * 50)
        print("Synthetic ID Tool (Interactive Menu)")
        print(f"System location: {tz_name} ({offset_str}) | {local_now.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        print("1. Batch generation (generate)")
        print("2. 17-digit checksum calculation (calc17)")
        print("3. 14-digit exhaustive search (exhaust14)")
        print("4. Exit")
        print("=" * 50)
        try:
            choice = input("Select function (1-4): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled. Exiting.")
            return 0

        if choice == '1':
            cnt_raw = input("Number of records (enter 'inf' for infinite mode, default 10): ").strip() or "10"
            if cnt_raw.lower() in ("inf", "infinite"):
                count = 0
                infinite = True
            else:
                infinite = False
                try:
                    count = int(cnt_raw)
                    if count < 0:
                        print("Invalid value. Using default 10.")
                        count = 10
                except ValueError:
                    print("Invalid input. Using default 10.")
                    count = 10
            start = input("Start date (YYYY-MM-DD) [default 2000-01-01]: ").strip() or "2000-01-01"
            end = input("End date (YYYY-MM-DD) [default 2020-01-01]: ").strip() or "2020-01-01"
            acf = input("Area-code file path (leave blank for sample codes): ").strip() or None
            allow_custom = False
            if acf:
                allow_custom = input("Allow custom area codes? Enter 'y' to confirm: ").strip().lower() == 'y'
            out = input("Output file (leave blank for no file): ").strip() or None
            ns = argparse.Namespace(
                count=count,
                infinite=infinite,
                start=start,
                end=end,
                area_codes_file=acf,
                allow_custom_area_codes=allow_custom,
                output=out,
                confirm=True,
            )
            try:
                cmd_generate(ns)
            except UserInterruptedToMenu as e:
                # The generation function already printed a message; just continue showing the menu.
                pass
            try:
                input("\nPress Enter to return to the main menu...")
            except (KeyboardInterrupt, EOFError):
                # Ignore and return to the menu immediately.
                pass
        elif choice == '2':
            val = input("Enter a 17-digit number: ").strip()
            ns = argparse.Namespace(value=val)
            try:
                cmd_calc17(ns)
            except UserInterruptedToMenu:
                pass
            try:
                input("\nPress Enter to return to the main menu...")
            except (KeyboardInterrupt, EOFError):
                pass
        elif choice == '3':
            val = input("Enter a 14-digit base number: ").strip()
            filt = input("Filter (male/female/all) [default all]: ").strip() or "all"
            out = input("Output file (leave blank for no file): ").strip() or None
            ns = argparse.Namespace(value=val, filter=filt, output=out, confirm=True)
            try:
                cmd_exhaust14(ns)
            except UserInterruptedToMenu:
                pass
            try:
                input("\nPress Enter to return to the main menu...")
            except (KeyboardInterrupt, EOFError):
                pass
        elif choice == '4':
            print("Exiting.")
            return 0
        else:
            print("Invalid option. Please enter 1-4.")


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_arg_parser()

    # If no CLI arguments are supplied (for example, when double-clicking the script), show the interactive menu.
    if argv is None and len(sys.argv) == 1:
        return interactive_mode()

    # Standard CLI path: parse arguments and execute the selected subcommand.
    args = parser.parse_args(argv)
    local_now, tz_name, offset_str = get_system_location_info()
    print(f"System location: {tz_name} ({offset_str}) | Current time: {local_now.strftime('%Y-%m-%d %H:%M:%S')}")
    print("Notice: This tool defaults to a conservative set of sample area codes. To use a custom source, use --area-codes-file together with --allow-custom-area-codes.")
    print("---------")
    try:
        if hasattr(args, "func"):
            try:
                return args.func(args)
            except UserInterruptedToMenu:
                # In CLI mode, Ctrl+C should return to the interactive menu instead of terminating the program.
                print("The current command was interrupted. Returning to the interactive menu.")
                return interactive_mode()
        else:
            # If no function is bound (for example, when no subcommand was supplied), show the interactive menu.
            return interactive_mode()
    except Exception as e:
        print(f"Unhandled exception: {e}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())