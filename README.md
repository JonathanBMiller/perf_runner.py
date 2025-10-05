# process_cpu_monitor.py

A lightweight CLI utility for monitoring CPU usage of a specific process by PID. Designed for snapshot inspection or sustained observation until the process reaches a defined rest state.

## Features

- Monitors CPU usage of a target process using `psutil`
- Supports single snapshot or continuous monitoring
- Detects rest state based on configurable thresholds
- Verbose output includes CPU times and process metadata
- Exit codes for scripting and automation

## Requirements

- Python 3.x
- [psutil](https://pypi.org/project/psutil/)

Install via pip:

```bash
pip install psutil
```

## Usage

```bash
python process_cpu_monitor.py -pid <PID> [options]
```

### Options

```text
-pid                     (Required) PID of the target process
-interval                Interval between samples (seconds). Default: 2
-max-count               Max cycles before giving up. Default: 800
-max-rest-count          Cycles required below rest threshold. Default: 10
-cpu-rest-value          CPU % considered "resting". Default: 30.0
-cpu-rest-reset-value    CPU % that resets rest counter. Default: 90.0
-wait-for-cpu-rest       Monitor until rest state is reached
-show-process-details    Show process info and exit
-verbose                 Enable detailed output
```

## Examples

Single snapshot:

```bash
python process_cpu_monitor.py -pid 1234
```

Wait for rest state:

```Win
python process_cpu_monitor.py -pid 4908 -wait-for-cpu-rest -verbose
============================================================
Monitoring process mysqld.exe at C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe
Rest threshold: 30.0% for 10 cycles
Reset threshold: 90.0%
Logical CPUs: 8
Physical CPUs: 4
CPU Frequency: 1596.00 MHz
============================================================
============================================================
Timestamp:         2025-09-28 16:59:21
Cycle:             1
Process Name:      mysqld.exe
Process Path:      C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe
CPU Usage:         0.00%
CPU Sys Time:      0.14
CPU User Time:     0.08
CPU Total Time:    0.22
Rest Counter:      1
Reset Counter:     0
============================================================
============================================================
Timestamp:         2025-09-28 16:59:24
Cycle:             2
Process Name:      mysqld.exe
Process Path:      C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe
CPU Usage:         0.00%
CPU Sys Time:      0.14
CPU User Time:     0.08
CPU Total Time:    0.22
Rest Counter:      2
Reset Counter:     0
============================================================
```

Verbose mode with custom thresholds:

```bash
python process_cpu_monitor.py -pid 1234 -verbose -cpu-rest-value 25.0 -cpu-rest-reset-value 85.0
```

## Output

Verbose output includes:

- Timestamp
- Cycle count
- Process name and path
- CPU usage (%)
- CPU system/user/total time
- Rest and reset counters

## Exit Codes

```text
0  Process reached rest state
1  Process did not reach rest state
2  No such process
3  Unknown error
```

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

## Author

Jonathan (Jeb) Miller