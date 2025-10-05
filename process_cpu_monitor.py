import psutil
import time
import argparse
import sys
import datetime

# Exit codes
REST = 0
NOT_REST = 1
NO_SUCH_PROCESS = 2
ERROR_UNKNOWN = 3

# Defaults
DEFAULT_MONITOR_INTERVAL = 2
DEFAULT_MAX_COUNT = 800
DEFAULT_MAX_REST_COUNT = 10
DEFAULT_CPU_REST_VALUE = 30.0
DEFAULT_CPU_RESET_REST_VALUE = 90.0

def to_screen(msg, verbose=False):
    if verbose:
        print(msg)

def show_cpu_info(verbose=False):
    to_screen(f"Logical CPUs: {psutil.cpu_count(logical=True)}", verbose)
    to_screen(f"Physical CPUs: {psutil.cpu_count(logical=False)}", verbose)
    freq = psutil.cpu_freq()
    if freq:
        to_screen(f"CPU Frequency: {freq.current:.2f} MHz", verbose)

def get_cpu_percentage(proc):
    proc.cpu_percent(interval=None)  # prime
    time.sleep(1)
    return proc.cpu_percent(interval=None)

def print_rest_snapshot(proc, percent, cpu_times, rest_count, reset_rest_counter, counter, verbose):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    to_screen("=" * 60, verbose)
    to_screen(f"Timestamp:         {timestamp}", verbose)
    to_screen(f"Cycle:             {counter}", verbose)
    to_screen(f"Process Name:      {proc.name()}", verbose)
    to_screen(f"Process Path:      {proc.exe()}", verbose)
    to_screen(f"CPU Usage:         {percent:.2f}%", verbose)
    to_screen(f"CPU Sys Time:      {cpu_times.system:.2f}", verbose)
    to_screen(f"CPU User Time:     {cpu_times.user:.2f}", verbose)
    to_screen(f"CPU Total Time:    {(cpu_times.system + cpu_times.user):.2f}", verbose)
    to_screen(f"Rest Counter:      {rest_count}", verbose)
    to_screen(f"Reset Counter:     {reset_rest_counter}", verbose)
    to_screen("=" * 60, verbose)

def print_rest_final(proc, counter, verbose):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    to_screen("=" * 60, verbose)
    to_screen(f"Timestamp:         {timestamp}", verbose)
    to_screen(f"Process Name:      {proc.name()}", verbose)
    to_screen(f"Process Path:      {proc.exe()}", verbose)
    to_screen(f"Reached rest after {counter} cycles", verbose)
    to_screen("=" * 60, verbose)

def show_process_details(proc, verbose):
    to_screen(f"Process name for pid {proc.pid} is {proc.name()}", verbose)
    to_screen(f"Process path for pid {proc.pid} is {proc.exe()}", verbose)
    show_cpu_info(verbose=verbose)
    try:
        percent = get_cpu_percentage(proc)
        cpu_times = proc.cpu_times()
        to_screen(f"CPU Usage:         {percent:.2f}%", verbose)
        to_screen(f"CPU Sys Time:      {cpu_times.system:.2f}", verbose)
        to_screen(f"CPU User Time:     {cpu_times.user:.2f}", verbose)
        to_screen(f"CPU Total Time:    {(cpu_times.system + cpu_times.user):.2f}", verbose)
    except Exception as e:
        to_screen(f"Error retrieving CPU stats: {e}", verbose)

def watch_for_rest(proc, args):
    rest_count = 0
    reset_rest_counter = 0
    counter = 0

    to_screen("=" * 60, args.verbose)
    to_screen(f"Monitoring process {proc.name()} at {proc.exe()}", args.verbose)
    to_screen(f"Rest threshold: {args.cpu_rest_value}% for {args.max_rest_count} cycles", args.verbose)
    to_screen(f"Reset threshold: {args.cpu_rest_reset_value}%", args.verbose)
    show_cpu_info(verbose=args.verbose)
    to_screen("=" * 60, args.verbose)

    while counter < args.max_count:
        try:
            percent = get_cpu_percentage(proc)
            cpu_times = proc.cpu_times()
        except psutil.NoSuchProcess:
            to_screen("No such process", args.verbose)
            return NO_SUCH_PROCESS
        except Exception as e:
            to_screen(f"Unknown error: {e}", args.verbose)
            return ERROR_UNKNOWN

        counter += 1

        if percent <= args.cpu_rest_value:
            if rest_count < args.max_rest_count:
                rest_count += 1
                print_rest_snapshot(proc, percent, cpu_times, rest_count, reset_rest_counter, counter, args.verbose)
            else:
                print_rest_final(proc, counter, args.verbose)
                return REST
        elif percent >= args.cpu_rest_reset_value:
            rest_count = 0
            reset_rest_counter += 1

        time.sleep(args.interval)

    to_screen("=" * 60, args.verbose)
    to_screen(f"Process did not reach rest state within {args.max_count} cycles.", args.verbose)
    to_screen("=" * 60, args.verbose)
    return NOT_REST

def main():
    parser = argparse.ArgumentParser(description="CPU usage monitor for a given PID")
    parser.add_argument("-pid", type=int, required=True)
    parser.add_argument("-interval", type=int, default=DEFAULT_MONITOR_INTERVAL)
    parser.add_argument("-max-count", type=int, default=DEFAULT_MAX_COUNT)
    parser.add_argument("-max-rest-count", type=int, default=DEFAULT_MAX_REST_COUNT)
    parser.add_argument("-cpu-rest-value", type=float, default=DEFAULT_CPU_REST_VALUE)
    parser.add_argument("-cpu-rest-reset-value", type=float, default=DEFAULT_CPU_RESET_REST_VALUE)
    parser.add_argument("-wait-for-cpu-rest", action="store_true")
    parser.add_argument("-show-process-details", action="store_true", help="Show full process info for the given PID and exit")
    parser.add_argument("-verbose", action="store_true")
    args = parser.parse_args()

    try:
        proc = psutil.Process(args.pid)
    except psutil.NoSuchProcess:
        to_screen(f"No such process with PID {args.pid}", args.verbose)
        sys.exit(NO_SUCH_PROCESS)

    if args.show_process_details:
        # Show mode overrides all other actions
        show_process_details(proc, True)
        sys.exit(0)

    if args.wait_for_cpu_rest:
        sys.exit(watch_for_rest(proc, args))

    # Default: single snapshot
    try:
        percent = get_cpu_percentage(proc)
        cpu_times = proc.cpu_times()
        print_rest_snapshot(proc, percent, cpu_times, rest_count=0, reset_rest_counter=0, counter=1, verbose=True)
        sys.exit(0)
    except psutil.NoSuchProcess:
        to_screen("No such process", args.verbose)
        sys.exit(NO_SUCH_PROCESS)
    except Exception as e:
        to_screen(f"Unknown error: {e}", args.verbose)
        sys.exit(ERROR_UNKNOWN)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        to_screen("\nInterrupted by user. Exiting.", verbose=True)
        sys.exit(ERROR_UNKNOWN)