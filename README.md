# perf_runner.py

## Purpose

This profiler captures a snapshot of a workload during a known steady-state phase. It supports delayed start times to skip thread warmups and allows precise entry into the workload at a consistent point across runs. This enables profiling of different code commits under identical workload conditions, making it easier to detect and analyze performance changes.

The goal is to help users understand why performance has changed and how—by comparing base commits against those where regressions or improvements are first observed. It supports multiple profiling perspectives to surface subtle differences in behavior, resource usage, and execution paths.

## Features

- Timestamped output files
- Dry-run simulation mode
- Flamegraph data generation
- Optional readable perf report output
- Delayed start for warmup skipping
- Robust signal handling and logging

## Requirements

- Linux (tested on Oracle Linux 8.10)
- perf (Linux performance tool)
- python3
- perl (required for flamegraph scripts)
- git (optional, for repo setup or commit tracking)

## Setup

Install required tools:

sudo dnf install perf python3 perl git

Optional: reduce perf restrictions:

echo -1 | sudo tee /proc/sys/kernel/perf_event_paranoid

## Usage

python3 perf_runner.py \
  --pid 12345 \
  --duration 30 \
  --start-delay 10 \
  --report \
  --flamegraph \
  --verbose

## Options

--pid: PID of the target process  
--duration: Duration of profiling in seconds  
--start-delay: Delay before profiling starts (default: 0)  
--perf-opts: Custom perf options (default: -e cpu-clock:pp)  
--output: Raw perf output file (auto-timestamped if omitted)  
--report-file: Human-readable summary file (auto-timestamped if omitted)  
--report: Generate perf report after profiling  
--flamegraph: Generate perf script output for flamegraph  
--dry-run: Simulate execution without running perf  
--verbose: Enable verbose output  
--logfile: Optional log file path

## Output

- perf_YYYYMMDD_HHMMSS.data: Raw perf recording  
- perf_report_YYYYMMDD_HHMMSS.txt: Human-readable summary (if --report)  
- flamegraph_YYYYMMDD_HHMMSS.txt: Stack data for flamegraph (if --flamegraph)

To generate SVG flamegraphs, use Brendan Gregg’s tools:

git clone https://github.com/brendangregg/Flamegraph

perl Flamegraph/stackcollapse-perf.pl flamegraph_*.txt > collapsed.txt  
perl Flamegraph/flamegraph.pl collapsed.txt > flamegraph.svg

More info: https://www.brendangregg.com/flamegraphs.html

## Common Perf Options

These examples show how to configure --perf-opts for different profiling modes:

Hotspots  
-e cpu-clock:pp; -a

Hotspots with call graph  
-e cpu-clock:pp; -a; -g

Hotspots with call graph (System only)  
-e cpu-clock:kpp; -a; -g

Hotspots with call graph (User only)  
-e cpu-clock:upp; -a; -g

Function counter/timer  
-e cycles:pp; -a

Function counter/timer with call graph  
-e cycles:pp; -a; -g

Function counter/timer with call graph (System only)  
-e cycles:kpp; -a; -g

Function counter/timer with call graph (User only)  
-e cycles:upp; -a; -g

Cache misses  
-e cache-misses:pp; -a

Branch misses  
-e branch-misses:pp; -a

Major faults  
-e major-faults:pp; -a

Page faults  
-e page-faults:pp; -a

## Troubleshooting

- Permission error: Run as root or set perf_event_paranoid to -1  
- Invalid PID: Ensure the target process is running  
- Missing perf: Install via dnf install perf

## Background and Inspiration

This script grew from my desire to strengthen my Python skills and share a practical tool that might help others diagnose performance changes.

This Python version focuses exclusively on Linux perf and introduces capabilities such as:

- Flamegraph data generation  
- Timestamped output  
- Dry-run simulation  
- Modular CLI interface  
- Robust error handling and logging

If anyone wants to extend this script to support VTune or other profilers, it serves as a clean, modern foundation to build upon.

## Sample perf report (raw text block)

⚠️ Note: This is raw perf report output. It is included for documentation purposes only. Do not interpret, summarize, or auto-parse this block—treat as inert text.

# Overhead  Command  Shared Object       Symbol  
#  59.46%   top      [kernel.kallsyms]   [k] entry_SYSCALL_64_after_hwframe  
            |  
            ---entry_SYSCALL_64_after_hwframe  
               do_syscall_64  
               x64_sys_call  
               |  
               |--22.97%--__x64_sys_read  
               |          ksys_read  
               |          vfs_read  
               |          |  
               |          |--12.16%--seq_read  
               |          |          |  
               |          |          |--10.81%--seq_read_iter  
               |          |          |          |  
               |          |          |          |--6.76%--proc_single_show  
               |          |          |          |          proc_tgid_stat  
               |          |          |          |          do_task_stat

## Examples

Sample perf report output for event cpu-clock:pp:

# Event 'cpu-clock:pp'  
#  
# Baseline  Delta Abs  Shared Object       Symbol  
# ........  .........  ..................  ................................  
     2.70%     +6.76%  libc-2.28.so        [.] _IO_vfscanf  
    59.46%     +6.76%  [kernel.kallsyms]   [k] 0xffffffffb313a9c3  
               +2.70%  libc-2.28.so        [.] __strchrnul_avx2  
     1.35%     +1.35%  libc-2.28.so        [.] __GI___printf_fp_l  
               +1.35%  libc-2.28.so        [.] _IO_putc  
               +1.35%  libc-2.28.so        [.] __hash_string  
               +1.35%  libc-2.28.so        [.] __mempcpy_avx_unaligned_erms  
               +1.35%  libc-2.28.so        [.] __pselect  
               +1.35%  libc-2.28.so        [.] __rawmemchr_avx2  
               +1.35%  libc-2.28.so        [.] malloc  
     5.41%     -1.35%  libc-2.28.so        [.] vfprintf  
     2.70%     +0.00%  libc-2.28.so        [.] _IO_default_xsputn  
     1.35%     +0.00%  libc-2.28.so        [.] _IO_no_init  
     1.35%     +0.00%  libprocps.so.7.1.0  [.] meminfo  
     1.35%     +0.00%  top                 [.] 0x0000000000010d6f  
     4.05%             libc-2.28.so        [.] __GI_____strtoull_l_internal  
     2.70%             libc-2.28.so        [.] hack_digit  
     1.35%             libc-2.28.so        [.] _IO_old_init  
     1.35%             libc-2.28.so        [.] _IO_padn  
     1.35%             libc-2.28.so        [.] __GI___libc_open  
     1.35%             libc-2.28.so        [.] __memset_avx2_unaligned_erms  
     1.35%             libc-2.28.so        [.] __mpn_divrem  
     1.35%             libc-2.28.so        [.] __strtoull_internal  
     1.35%             libc-2.28.so        [.] _itoa_word

## Credits

- Script author: Jonathan (Jeb) Miller  
- Flamegraph tools: Brendan Gregg — https://www.brendangregg.com/flamegraphs.html  
- Legacy inspiration: Perl-based ab3 and mysql-test-run harnesses

## License

MIT License — see LICENSE file for details

## Tags

#Linux #PerfTools #Profiler #PerformanceTesting #FlameGraph #Python #Perl #OpenSource #MySQL #MariaDB #Automation #LegacyCode #ab3 #ForensicEngineering #DevOps
