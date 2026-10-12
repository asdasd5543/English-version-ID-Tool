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
from datetime import datetime, timedelta
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
    local_now = datetime.now()
    is_dst = time.localtime().tm_isdst
    try:
        tz_name = time.tzname[1] if is_dst else time.tzname[0]
    except Exception:
        tz_name = "Local"
    utc_offset_seconds = (datetime.now() - datetime.utcnow()).total_seconds()
    utc_offset_hours = utc_offset_seconds / 3600.0
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
            friendly_birthday = target_date.strftime("%Y年%m月%d日")
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
            friendly_birthday = target_date.strftime("%Y年%m月%d日")
            sequence_num = str(random.randint(0, 999)).zfill(3)
            front_17 = f"{area}{birthday_str}{sequence_num}"
            check_char = calculate_check_digit(front_17)
            full_id = front_17 + check_char
            yield full_id, friendly_birthday, area


def cmd_generate(args: argparse.Namespace) -> int:
    """
    Generate ID number samples in batches.
    - 如果 args.infinite 为 True，则无限生成直到 Ctrl+C（必须确认）
    - 若输出到文件，在Infinite mode下采取流式写入
    在捕获到 KeyboardInterrupt 时抛出 UserInterruptedToMenu，以便返回交互式菜单而不是Exit程序。
    """
    is_infinite = bool(getattr(args, "infinite", False))
    # 确认保护：Infinite mode必须确认，有限模式若未确认也弹交互确认
    if is_infinite or not getattr(args, "confirm", False):
        print("警告：Batch generation of ID numbers may be sensitive and is limited to academic/testing/simulation purposes.")
        if not getattr(args, "confirm", False):
            try:
                ans = input("Continue? Enter y to confirm: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print("\nCancelled.")
                return 1
            if ans != 'y':
                print("Cancelled.")
                return 1

    # 加载区域码（若提供文件则优先）
    if getattr(args, "area_codes_file", None):
        try:
            area_codes = load_area_codes_from_file(Path(args.area_codes_file))
            if not area_codes:
                print("No area codes loaded from file. Exiting.")
                return 1
        except Exception as e:
            print(f"Failed to load area code file: {e}")
            return 1
    else:
        area_codes = _DEFAULT_AREA_CODES

    # 解析日期
    try:
        start_date = datetime.strptime(getattr(args, "start", "2000-01-01"), "%Y-%m-%d")
        end_date = datetime.strptime(getattr(args, "end", "2020-01-01"), "%Y-%m-%d")
    except ValueError as e:
        print(f"Invalid date format: {e}")
        return 1

    # Determine count: None means infinite
    count_param: Optional[int] = None if is_infinite else int(getattr(args, "count", 10))

    generated = 0

    # 如果输出到文件且是Infinite mode，使用流式写入
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
        # 捕获 Ctrl+C：不要Exit程序，转为返回主菜单
        if outfile:
            try:
                outfile.flush()
            except Exception:
                pass
        print(f"\n[⚠️] Interrupted by user. Generated {generated} records. Returning to main menu...")
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
        print(f"Completed: generated {generated} records (range: {getattr(args, 'start', '2000-01-01')} 至 {getattr(args, 'end', '2020-01-01')}）。")
    else:
        print(f"Infinite mode结束：本次共生成 {generated} 条记录（正常结束）")
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
    gender_symbol = "🚹 Male" if gender_digit % 2 != 0 else "🚺 Female"

    print("-" * 50)
    print(f"📅 Birthday : {year}年 {month}月 {day}日")
    print(f"🧬 Gender : {gender_symbol}")
    print(f"🧠 18th digit checksum : {check_char}")
    print(f"🆔 Full sequence : {s}{check_char}")
    print("-" * 50)
    return 0


def cmd_exhaust14(args: argparse.Namespace) -> int:
    base = args.value.strip()
    if len(base) != 14 or not base.isdigit():
        print("错误：Please enter exactly 14 digits.")
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
            gender_symbol = "🚹 Male" if is_male else "🚺 Female"
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
        description="ID number sequence tool (restricted, safe defaults)",
        epilog="Disclaimer: For educational/testing/simulation purposes only. Illegal use is strictly prohibited.",
    )
    p.add_argument("--version", action="version", version="id-tool 1.3")
    sub = p.add_subparsers(dest="cmd")

    gen = sub.add_parser("generate", help="Generate ID samples (controlled)")
    gen.add_argument("--count", type=int, default=10, help="Number of records (default 10, --infinite takes priority)")
    gen.add_argument("--infinite", action="store_true", help="Enable infinite generation until interrupted (confirmation required)")
    gen.add_argument("--start", default="2000-01-01", help="Start date (YYYY-MM-DD)，默认 2000-01-01")
    gen.add_argument("--end", default="2020-01-01", help="End date (YYYY-MM-DD)，默认 2020-01-01 (不含)")
    gen.add_argument("--area-codes-file", default=None, help="Area code file path (CSV or one code per line)")
    gen.add_argument("--output", default=None, help="Optional: output to file (CSV format)")
    gen.add_argument("--confirm", action="store_true", help="Skip interactive confirmation")
    gen.set_defaults(func=cmd_generate)

    c17 = sub.add_parser("calc17", help="Calculate 18th checksum digit and parse birthday/gender (17 digits input)")
    c17.add_argument("value", help="17-digit number")
    c17.set_defaults(func=cmd_calc17)

    ex = sub.add_parser("exhaust14", help="Exhaust 000-999 sequences from 14-digit base (gender filtering available)")
    ex.add_argument("value", help="14-digit base number")
    ex.add_argument("--filter", default="all", help="Filter: male / female / all (default all)")
    ex.add_argument("--output", default=None, help="可选：输出到文件 (CSV)")
    ex.add_argument("--confirm", action="store_true", help="Skip interactive confirmation")
    ex.set_defaults(func=cmd_exhaust14)

    return p


def interactive_mode() -> int:
    """
    交互式菜单（当用户双击或未提供 CLI 参数时使用）
    捕获并处理 UserInterruptedToMenu，以确保 Ctrl+C 不会Exit程序。
    """
    while True:
        local_now, tz_name, offset_str = get_system_location_info()
        print("\n" + "=" * 50)
        print("🎛️  Automated Data Control Center (Interactive)")
        print(f"🌐 Node location: {tz_name} ({offset_str}) | {local_now.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        print("1. Batch generation (generate)")
        print("2. 17-digit checksum calculation (calc17)")
        print("3. 14-digit exhaustive search (exhaust14)")
        print("4. Exit")
        print("=" * 50)
        try:
            choice = input("Select function (1-4): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n已取消，Exit。")
            return 0

        if choice == '1':
            # 支持输入 inf/infinite 表示无限生成
            cnt_raw = input("Number of records (enter inf for infinite, default 10):: ").strip() or "10"
            if cnt_raw.lower() in ("inf", "infinite"):
                count = 0  # placeholder
                infinite = True
            else:
                infinite = False
                try:
                    count = int(cnt_raw)
                    if count < 0:
                        print("无效数字，使用默认 10。")
                        count = 10
                except ValueError:
                    print("无效输入，使用默认 10。")
                    count = 10
            start = input("Start date (YYYY-MM-DD) [默认 2000-01-01]: ").strip() or "2000-01-01"
            end = input("End date (YYYY-MM-DD) [默认 2020-01-01]: ").strip() or "2020-01-01"
            acf = input("Area code file path (leave empty for example codes): ").strip() or None
            out = input("Output file (leave empty for no file): ").strip() or None
            # 构造 Namespace 与调用
            ns = argparse.Namespace(
                count=count,
                infinite=infinite,
                start=start,
                end=end,
                area_codes_file=acf,
                output=out,
                confirm=True,  # 交互模式默认跳过二次确认以便顺畅体验
            )
            try:
                cmd_generate(ns)
            except UserInterruptedToMenu as e:
                # 已在 cmd_generate 中打印提示，这里仅让交互继续
                pass
            # 等待用户回到菜单：即便用户在生成时按过 Ctrl+C，也不要因为上次 Ctrl+C 而跳过这个等待
            try:
                input("\nPress Enter to return to main menu...")
            except (KeyboardInterrupt, EOFError):
                # 忽略，直接回到菜单
                pass
        elif choice == '2':
            val = input("请输入 17-digit number: ").strip()
            ns = argparse.Namespace(value=val)
            try:
                cmd_calc17(ns)
            except UserInterruptedToMenu:
                pass
            try:
                input("\nPress Enter to return to main menu...")
            except (KeyboardInterrupt, EOFError):
                pass
        elif choice == '3':
            val = input("请输入 14-digit base number: ").strip()
            filt = input("Filter (male/female/all) [default all]: ").strip() or "all"
            out = input("Output file (leave empty for no file): ").strip() or None
            ns = argparse.Namespace(value=val, filter=filt, output=out, confirm=True)
            try:
                cmd_exhaust14(ns)
            except UserInterruptedToMenu:
                pass
            try:
                input("\nPress Enter to return to main menu...")
            except (KeyboardInterrupt, EOFError):
                pass
        elif choice == '4':
            print("Exit。")
            return 0
        else:
            print("Invalid option. Please enter 1-4.")


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_arg_parser()

    # 如果没有提供命令行参数（例如双击运行或直接 python script.py），进入交互式菜单
    if argv is None and len(sys.argv) == 1:
        return interactive_mode()

    # 常规 CLI 路径：解析并执行子命令
    args = parser.parse_args(argv)
    local_now, tz_name, offset_str = get_system_location_info()
    print(f"节点: {tz_name} ({offset_str}) | Current time: {local_now.strftime('%Y-%m-%d %H:%M:%S')}")
    print("注意：本工具默认使用较保守的示例区域码，如需真实区域码，请提供 --area-codes-file。")
    print("---------")
    try:
        if hasattr(args, "func"):
            try:
                return args.func(args)
            except UserInterruptedToMenu:
                # 在 CLI 模式下按 Ctrl+C 也不要直接Exit程序，转而进入交互式菜单
                print("已中止当前命令，进入交互式菜单。")
                return interactive_mode()
        else:
            # 如果没有 func（例如没有子命令），进入交互式模式
            return interactive_mode()
    except Exception as e:
        print(f"Unhandled exception: {e}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())