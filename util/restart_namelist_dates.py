#!/usr/bin/env python3
#
# Description:
#   Automatically detects the most recently modified valid WRF restart file
#   and updates the simulation dates in namelist.input accordingly.
#
#   The script checks whether restart mode is enabled, validates the number
#   of configured domains, searches for valid restart files, and extracts
#   the restart date from the selected filename.
#
#   The following variables in the &time_control section are updated:
#     - start_year
#     - start_month
#     - start_day
#     - end_year
#
# Features:
#   - Checks whether restart = .true. is enabled.
#   - Supports 1 to 3 WRF domains.
#   - Validates restart files using the NetCDF4 library.
#   - Selects the most recently modified valid restart file.
#   - Updates dates for all configured domains.
#   - Preserves unrelated namelist settings and comments where possible.
#   - Avoids modifying namelist.input if restart is disabled or no valid
#     restart file is found.
#
# Requirements:
#   - Python 3
#   - netCDF4
#   - NumPy
#
# Configuration:
#   FOLDER_PATH      Directory containing namelist.input and restart files.
#   NAMELIST         Path to the WRF namelist.input file.
#   RESTART_PATTERN  Pattern used to locate WRF restart files.
#
# Usage:
#   Run the script from the WRF run directory:
#     python3 update_wrf_restart_dates.py
#
# Important:
#   - The script modifies namelist.input in place.
#   - The restart date is extracted from the filename.
#   - The most recently modified valid file is selected, which may not
#     correspond to the latest simulation timestamp.
#   - The script does not verify that restart files for all domains belong
#     to the same checkpoint.
#
# Original:
#    https://github.com/CORDEX-WRF-community/euro-cordex-cmip6/blob/main/util/update_and_restart.py
# Contact: milovacj@unican.es
# Original created: [03-12-2023]
# Revised and extended: [16-10-2026]
# =============================================================================


import os
import re
import sys
import glob
import calendar
import netCDF4 as nc

from datetime import datetime

# ============================================================
# Configuration
# ============================================================
FOLDER_PATH = "./"
NAMELIST = os.path.join(FOLDER_PATH, "namelist.input")
RESTART_PATTERN = "wrfrst_d{domain}_*"

# ============================================================
# Helper functions
# ============================================================

def read_lines(file_path):
    with open(file_path, "r") as file:
        return file.readlines()


def write_lines(file_path, lines):
    with open(file_path, "w") as file:
        file.writelines(lines)


def get_active_line(line):
    """Remove comments while preserving active namelist content."""
    return line.split("!")[0].strip()


def get_namelist_value(lines, variable):
    """
    Read a scalar namelist value, ignoring comments and
    matching variable names exactly.
    """
    pattern = re.compile(
        rf"^\s*{re.escape(variable)}\s*=\s*(.*?)\s*,?\s*$",
        re.IGNORECASE
    )

    for line in lines:
        active = get_active_line(line)
        match = pattern.match(active)

        if match:
            return match.group(1).strip()

    return None


def get_restart():
    """Read the logical restart variable from namelist.input."""

    pattern = re.compile(
        r"^\s*restart\s*=\s*(\.true\.|\.false\.|true|false|[TtFf])",
        re.IGNORECASE,
    )

    with open(NAMELIST, "r") as file:
        for line in file:
            # Remove inline Fortran comments.
            line = line.split("!", 1)[0].strip()

            if not line or line.startswith("#"):
                continue

            match = pattern.match(line)

            if match:
                value = match.group(1).strip().lower()
                return value in (".true.", "true", "t")

    # Default if restart is not specified.
    return False


def get_max_dom(lines):
    """Read and validate max_dom."""
    value = get_namelist_value(lines, "max_dom")

    if value is None:
        raise ValueError("max_dom was not found in namelist.input.")

    # max_dom must be a single integer.
    match = re.match(r"^\s*(\d+)\s*$", value)

    if not match:
        raise ValueError(f"Invalid max_dom value: {value}")

    max_dom = int(match.group(1))

    if max_dom not in (1, 2, 3):
        raise ValueError(
            f"Unsupported max_dom={max_dom}. Expected 1, 2, or 3."
        )

    return max_dom

def get_restart_date(filename):
    """Extract date from WRF restart filenames with _ or : time separators."""
    match = re.search(
        r"wrfrst_d0[1-3]_(\d{4}-\d{2}-\d{2})"
        r"(?:_(\d{2})[_:](\d{2})[_:](\d{2}))?",
        os.path.basename(filename)
    )

    if not match:
        return None

    try:
        return datetime.strptime(match.group(1), "%Y-%m-%d")
    except ValueError:
        return None


def is_valid_restart_file(filepath):
    """
    Verify that the file can be opened as NetCDF and that
    it contains a valid WRF Times variable when available.
    """
    try:
        with nc.Dataset(filepath, "r") as dataset:

            if "Times" in dataset.variables:
                times = dataset.variables["Times"]

                if times.size == 0:
                    return False

                # Read at least one timestamp to detect
                # unreadable or truncated variable data.
                timestamp = times[0]

                if np_all_empty(timestamp):
                    return False

            return True

    except Exception as error:
        print(f"Skipping invalid restart file: {filepath}")
        print(f"  Reason: {error}")
        return False


def np_all_empty(value):
    """Check whether a NetCDF timestamp contains any characters."""
    import numpy as np

    try:
        return len(np.asarray(value).tobytes().strip(b"\x00 ")) == 0
    except Exception:
        return False



def find_latest_restart(max_dom):
    """Find the latest readable restart file for configured domains."""

    candidates = []

    for domain_number in range(1, max_dom + 1):
        domain = f"d{domain_number:02d}"
        pattern = os.path.join(FOLDER_PATH, f"wrfrst_{domain}_*")

        files = glob.glob(pattern)
        print(f"Searching {pattern}: found {len(files)} file(s)")

        for filepath in files:
            restart_date = get_restart_date(filepath)

            if restart_date is None:
                print(f"  Cannot extract date: {filepath}")
                continue

            candidates.append((filepath, restart_date))

    # Sort by modification time, newest first.
    candidates.sort(
        key=lambda item: os.path.getmtime(item[0]),
        reverse=True
    )

    for filepath, restart_date in candidates:
        print(f"Checking NetCDF file: {filepath}")

        if is_valid_restart_file(filepath):
            print(f"  Valid restart file: {filepath}")
            return filepath, restart_date

    print("No valid restart file found.")
    return None, None


def update_namelist_dates(lines, restart_date, max_dom):
    """
    Update start_year/month/day and end_year for all configured
    domains. Keep the original formatting and other settings.
    """
    replacements = {
        "start_year": [restart_date.year] * max_dom,
        "start_month": [restart_date.month] * max_dom,
        "start_day": [restart_date.day] * max_dom,
        "end_year": [restart_date.year + 1] * max_dom,
    }

    updated_lines = []
    in_time_control = False

    for line in lines:
        active = get_active_line(line)

        if active.startswith("&"):
            in_time_control = (
                active[1:].strip().lower() == "time_control"
            )
            updated_lines.append(line)
            continue

        if active.startswith("/"):
            in_time_control = False
            updated_lines.append(line)
            continue

        if not in_time_control:
            updated_lines.append(line)
            continue

        match = re.match(
            r"^(\s*)(start_year|start_month|start_day|end_year)"
            r"(\s*=\s*)(.*?)(\s*(?:!.*)?(?:\r?\n)?)$",
            line,
            re.IGNORECASE
        )

        if match:
            indent, variable, separator, _, suffix = match.groups()
            key = variable.lower()

            if key in replacements:
                values = replacements[key]
                value_string = ", ".join(
                    f"{value:02d}" if key in
                    ("start_month", "start_day") else str(value)
                    for value in values
                )

                updated_lines.append(
                    f"{indent}{variable}{separator}"
                    f"{value_string},{suffix}"
                )
                continue

        updated_lines.append(line)

    return updated_lines


# ============================================================
# Main
# ============================================================

def main():
    if not os.path.isfile(NAMELIST):
        print(f"ERROR: {NAMELIST} was not found.")
        sys.exit(1)

    lines = read_lines(NAMELIST)

    # 1. Check restart setting before making any changes.
    if not get_restart():
        print("Restart is false or missing. No changes made.")
        return

    print("Restart is enabled.")

    # 2. Read the number of configured domains.
    try:
        max_dom = get_max_dom(lines)
    except ValueError as error:
        print(f"ERROR: {error}")
        sys.exit(1)

    print(f"Configured domains: {max_dom}")

    # 3. Find the latest valid restart file.
    restart_file, restart_date = find_latest_restart(max_dom)

    if restart_file is None:
        print("ERROR: No valid restart file was found.")
        print("namelist.input was not modified.")
        sys.exit(1)

    print(f"Selected restart file: {restart_file}")
    print(f"Restart date: {restart_date:%Y-%m-%d}")

    # 4. Update the date fields for all configured domains.
    updated_lines = update_namelist_dates(
        lines,
        restart_date,
        max_dom
    )

    # 5. Save the changes.
    write_lines(NAMELIST, updated_lines)

    print("namelist.input updated successfully.")
    print(f"Domains updated: d01 through d{max_dom:02d}")
    print(f"Start date: {restart_date:%Y-%m-%d}")
    print(f"End year: {restart_date.year + 1}")


if __name__ == "__main__":
    main()

