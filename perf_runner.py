#!/usr/bin/env python3

import argparse
import os
import subprocess
import time
import logging
import sys
from datetime import datetime
import pwd

def check_perf_access_or_root():
    try:
        with open("/proc/sys/kernel/perf_event_paranoid", "r") as f:
            val = int(f.read().strip())
            if val > -1 and os.geteuid() != 0:
                sys.exit("Root privileges required unless perf_event_paranoid is set to -1")
    except Exception as e:
        sys.exit(f"Perf access check failed: {e}")

def validate_pid(pid):
    return os.path.exists(f"/proc/{pid}")

def timestamped_name(base, ext):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base}_{ts}.{ext}"

def is_root():
    return os.geteuid() == 0

def fix_ownership(path, verbose=False):
    target_user = os.environ.get("SUDO_USER", os.environ.get("USER"))
    try:
        pw_record = pwd.getpwnam(target_user)
        uid = pw_record.pw_uid
        gid = pw_record.pw_gid
        os.chown(path, uid, gid)
        if verbose:
            print(f"Changed ownership of {path} to {target_user}")
    except Exception as e:
        print(f"Failed to change ownership of {path}: {e}")

def run_perf(pid, duration, perf_opts, output_file, verbose, dry_run):
    cmd = ["perf", "record"] + perf_opts.split() + [
        "-p", str(pid),
        "-o", output_file,
        "--", "sleep", str(duration)
    ]
    if verbose or dry_run:
        print(f"Running: {' '.join(cmd)}")
    if not dry_run:
        subprocess.run(cmd, check=True)
        if is_root():
            fix_ownership(output_file, verbose)

def generate_report(output_file, report_file, verbose, dry_run):
    cmd = ["perf", "report", "-i", output_file, "--stdio", "-f"]
    if verbose or dry_run:
        print(f"Generating report: {' '.join(cmd)}")
    if not dry_run:
        with open(report_file, "w") as f:
            subprocess.run(cmd, stdout=f, check=True)

def generate_flamegraph_data(output_file, flamegraph_file, verbose, dry_run):
    cmd = ["perf", "script", "-i", output_file]

    try:
        stat_info = os.stat(output_file)
        current_uid = os.geteuid()
        current_gid = os.getegid()
        if stat_info.st_uid != current_uid and stat_info.st_uid != 0:
            if verbose:
                print(f"Ownership mismatch: file owned by UID {stat_info.st_uid}, current UID is {current_uid}. Adding -f.")
            cmd.append("-f")
        elif stat_info.st_gid != current_gid and stat_info.st_gid != 0:
            if verbose:
                print(f"Group mismatch: file owned by GID {stat_info.st_gid}, current GID is {current_gid}. Adding -f.")
            cmd.append("-f")
    except Exception as e:
        print(f"Ownership check failed: {e}. Proceeding with -f as fallback.")
        cmd.append("-f")

    if verbose or dry_run:
        print(f"Generating flamegraph data: {' '.join(cmd)}")
    if not dry_run:
        with open(flamegraph_file, "w") as f:
            subprocess.run(cmd, stdout=f, check=True)

def main():
    parser = argparse.ArgumentParser(description="Linux perf profiler runner")
    parser.add_argument("--pid", type=int, required=True, help="PID to profile")
    parser.add_argument("--duration", type=int, required=True, help="Duration in seconds")
    parser.add_argument("--start-delay", type=int, default=0, help="Delay before profiling starts")
    parser.add_argument("--perf-opts", default="-e cpu-clock:pp", help="Perf options string")
    parser.add_argument("--output", help="Raw perf output file (timestamped if not set)")
    parser.add_argument("--report-file", help="Readable summary file (timestamped if not set)")
    parser.add_argument("--report", action="store_true", help="Generate report after profiling")
    parser.add_argument("--flamegraph", action="store_true", help="Generate perf script output for flamegraph")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without running perf")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--logfile", help="Optional log file")

    args = parser.parse_args()

    if args.logfile:
        logging.basicConfig(filename=args.logfile, level=logging.INFO)
    elif args.verbose:
        logging.basicConfig(level=logging.INFO)

    logging.info("Starting perf_runner")

    check_perf_access_or_root()

    if not validate_pid(args.pid):
        sys.exit(f"PID {args.pid} is not valid or not running.")

    if args.start_delay > 0:
        logging.info(f"Waiting {args.start_delay} seconds before starting profiling...")
        time.sleep(args.start_delay)

    output_file = args.output or timestamped_name("perf", "data")
    report_file = args.report_file or timestamped_name("perf_report", "txt")
    flamegraph_file = timestamped_name("flamegraph", "txt") if args.flamegraph else None

    try:
        run_perf(args.pid, args.duration, args.perf_opts, output_file, args.verbose, args.dry_run)
        if args.report:
            generate_report(output_file, report_file, args.verbose, args.dry_run)
        if args.flamegraph:
            generate_flamegraph_data(output_file, flamegraph_file, args.verbose, args.dry_run)
    except subprocess.CalledProcessError as e:
        sys.exit(f"Perf execution failed: {e}")

    logging.info("Profiling complete.")

if __name__ == "__main__":
    try:
        while True:
            main()
            print("\nRun complete.")
            response = input("Run again? [y/N]: ").strip().lower()
            if response != "y":
                print("Exiting perf_runner.")
                break
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting cleanly.")
        logging.info("Execution interrupted by user.")
        sys.exit(130)