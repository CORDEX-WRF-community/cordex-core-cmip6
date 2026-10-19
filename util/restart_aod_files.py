#!/usr/bin/env python3
#==============================================================================
# Script: update_aod.py
#
# Description:
#    Update WRF Aerosol Optical Depth (AOD) input files for all domains
#    specified by max_dom in namelist.input.
#
# Steps:
#    1. Read start date, end date, restart, and max_dom from namelist.input.
#    2. If restart is true, advance the effective start date by one day.
#    3. Process domains d01, d02, ..., up to max_dom.
#    4. Locate yearly AOD files covering the simulation period.
#    5. Use one yearly file if the period is within one year.
#       Merge yearly files if the period spans multiple years.
#    6. Extract AOD records from the effective start date through the end date.
#    7. Save output as AOD_<DOMAIN>.
#
# Calendar options:
#    standard : Gregorian calendar, including leap years.
#    no-leap  : 365-day calendar, without February 29.
#    365-days : 365-day calendar, without February 29.

# Requirements:
#    - Python 3
#    - NCO utilities: ncrcat and ncks
#    - namelist.input
#    - Yearly AOD NetCDF files

# Note:
#    Assumes yearly AOD files contain complete years of daily records,
#    starting on January 1, and are ordered chronologically.
#    namelist.input and MPTABLE.TBL are not modified.
    
# Original:
#    https://github.com/CORDEX-WRF-community/euro-cordex-cmip6/blob/main/util/update_and_restart.py

# Contact: milovacj@unican.es
# Original created: [03-12-2023]
# Updated: [16-10-2026]
===============================================================================

import calendar
import glob
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path


# =============================================================================
# Configuration
# =============================================================================

AOD_DIR = Path("../../../data/input/AOD_files/")
NAMELIST = Path("./namelist.input")

# Calendar options: "standard", "no-leap", or "365-days"
CALENDAR = "standard"


# =============================================================================
# Helper functions
# =============================================================================

def read_namelist_value(variable):
    """Read an integer variable from namelist.input."""

    pattern = re.compile(
        rf"^\s*{re.escape(variable)}\s*=\s*([^,!]+)",
        re.IGNORECASE,
    )

    with open(NAMELIST, "r") as file:
        for line in file:
            # Remove inline comments.
            line = line.split("!", 1)[0]

            if line.lstrip().startswith("#"):
                continue

            match = pattern.match(line)

            if match:
                return int(match.group(1).strip())

    raise ValueError(
        f"Variable '{variable}' not found in {NAMELIST}."
    )

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


def get_start_date():
    """Read the simulation start date."""

    return datetime(
        read_namelist_value("start_year"),
        read_namelist_value("start_month"),
        read_namelist_value("start_day"),
    )


def get_end_date():
    """Read the simulation end date."""

    return datetime(
        read_namelist_value("end_year"),
        read_namelist_value("end_month"),
        read_namelist_value("end_day"),
    )


def get_number_of_domains():
    """Read max_dom from namelist.input."""

    max_dom = read_namelist_value("max_dom")

    if max_dom < 1:
        raise ValueError(
            f"Invalid max_dom={max_dom}. It must be at least 1."
        )

    return max_dom


def get_calendar():
    """Validate and return the configured calendar."""

    calendar_type = CALENDAR.strip().lower()

    if calendar_type not in ("standard", "no-leap", "365-days"):
        raise ValueError(
            f"Unsupported CALENDAR='{CALENDAR}'. "
            "Choose 'standard', 'no-leap', or '365-days'."
        )

    return calendar_type


def is_no_leap():
    """Check whether the selected calendar excludes leap days."""

    return get_calendar() in ("no-leap", "365-days")


def validate_calendar_date(date):
    """Validate a date against the selected calendar."""

    if is_no_leap() and calendar.isleap(date.year):
        if date.month == 2 and date.day == 29:
            raise ValueError(
                f"{date:%Y-%m-%d} is not valid for "
                f"the {CALENDAR} calendar."
            )


def advance_calendar_day(date):
    """Advance one day according to the selected calendar."""

    next_date = date + timedelta(days=1)

    # Skip February 29 in no-leap calendars.
    if is_no_leap():
        if next_date.month == 2 and next_date.day == 29:
            next_date += timedelta(days=1)

    return next_date


def calendar_day_of_year(date):
    """Return the zero-based daily record index within a year."""

    validate_calendar_date(date)

    day_index = date.timetuple().tm_yday - 1

    if is_no_leap():
        if calendar.isleap(date.year) and date.month > 2:
            day_index -= 1

    return day_index


def days_between_dates(start_date, end_date):
    """Count calendar days between dates, inclusive."""

    if end_date < start_date:
        raise ValueError(
            f"End date {end_date:%Y-%m-%d} is earlier than "
            f"start date {start_date:%Y-%m-%d}."
        )

    validate_calendar_date(start_date)
    validate_calendar_date(end_date)

    number_of_days = (end_date - start_date).days + 1

    if is_no_leap():
        for year in range(start_date.year, end_date.year + 1):
            if calendar.isleap(year):
                leap_day = datetime(year, 2, 29)

                if start_date <= leap_day <= end_date:
                    number_of_days -= 1

    return number_of_days


def find_aod_file(year, domain):
    """Find the yearly AOD file for a given year and domain."""

    pattern = str(AOD_DIR / f"AOD*_{year}*{domain}*")
    files = sorted(glob.glob(pattern))

    if not files:
        raise FileNotFoundError(
            f"No AOD file found for year {year}, domain {domain}.\n"
            f"Expected pattern: {pattern}"
        )

    if len(files) > 1:
        print(
            f"WARNING: Multiple AOD files match year {year}, "
            f"domain {domain}. Using the first match:\n"
            f"  {files[0]}"
        )

    return files[0]


# =============================================================================
# Update AOD file for one domain
# =============================================================================

def update_aod(domain, start_date, end_date):
    """Create the AOD input file for one WRF domain."""

    print("\n" + "=" * 70)
    print(f"UPDATE AOD FILE: {domain}")
    print("=" * 70)

    if end_date < start_date:
        raise ValueError(
            f"End date {end_date:%Y-%m-%d} is earlier than "
            f"effective start date {start_date:%Y-%m-%d}."
        )

    validate_calendar_date(start_date)
    validate_calendar_date(end_date)

    start_year = start_date.year
    end_year = end_date.year

    start_time = start_date.strftime("%Y-%m-%d")
    end_time = end_date.strftime("%Y-%m-%d")

    simulation_days = days_between_dates(start_date, end_date)

    # Daily records are assumed to start on January 1 of start_year.
    start_index = calendar_day_of_year(start_date)
    end_index = start_index + simulation_days - 1

    aod_output = Path(f"AOD_{domain}")
    merged_output = Path(f"merged_{domain}.nc")

    print(f"Domain:          {domain}")
    print(f"Calendar:        {CALENDAR}")
    print(f"Start date:      {start_time}")
    print(f"End date:        {end_time}")
    print(f"Number of days:  {simulation_days}")
    print(f"Start year:      {start_year}")
    print(f"End year:        {end_year}")
    print(f"Time indices:    {start_index} to {end_index}")

    # Locate all yearly files required for the simulation.
    yearly_files = []

    for year in range(start_year, end_year + 1):
        aod_file = find_aod_file(year, domain)
        yearly_files.append(aod_file)
        print(f"AOD file ({year}): {aod_file}")

    merged_created = False

    try:
        # Merge files only when the simulation spans multiple years.
        if start_year != end_year:
            if merged_output.exists():
                merged_output.unlink()

            print("Merging yearly AOD files...")

            subprocess.run(
                [
                    "ncrcat",
                    *yearly_files,
                    str(merged_output),
                ],
                check=True,
            )

            source_file = merged_output
            merged_created = True

        else:
            # Single-year simulation: use the yearly file directly.
            source_file = Path(yearly_files[0])

        # Remove an existing output before creating a new one.
        if aod_output.exists():
            aod_output.unlink()

        # Extract the requested period, inclusive.
        time_range = f"Time,{start_index},{end_index}"

        subprocess.run(
            [
                "ncks",
                "-O",
                "-d",
                time_range,
                str(source_file),
                str(aod_output),
            ],
            check=True,
        )

        print("-" * 70)
        print(f"AOD file successfully created: {aod_output}")
        print(f"Requested period: {start_time} to {end_time}")
        print(f"Number of days requested: {simulation_days}")

    finally:
        # Remove the temporary merged file.
        if merged_created and merged_output.exists():
            merged_output.unlink()

    print(f"Finished processing {domain}.")


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    try:
        # Read configuration from namelist.input.
        start_date = get_start_date()
        end_date = get_end_date()
        max_dom = get_number_of_domains()
        restart = get_restart()
        get_calendar()

        # Validate the dates before adjusting the restart start date.
        validate_calendar_date(start_date)
        validate_calendar_date(end_date)

        if end_date < start_date:
            raise ValueError(
                "The simulation end date is earlier than "
                "the start date in namelist.input."
            )

        original_start_date = start_date

        # A restart file already contains the initial restart date.
        # Start extracting AOD from the following calendar day.
        if restart:
            start_date = advance_calendar_day(start_date)

            print(
                "Restart enabled: advancing the effective AOD "
                "start date by one calendar day."
            )

        if end_date < start_date:
            raise ValueError(
                "The effective start date is later than the end date. "
                "Check restart and the simulation dates."
            )

        total_days = days_between_dates(start_date, end_date)

        print("=" * 70)
        print("WRF AOD UPDATE")
        print("=" * 70)
        print(f"Calendar:            {CALENDAR}")
        print(f"Restart:             {restart}")
        print(f"Namelist start:      {original_start_date:%Y-%m-%d}")
        print(f"Effective AOD start: {start_date:%Y-%m-%d}")
        print(f"Simulation end:      {end_date:%Y-%m-%d}")
        print(f"Number of domains:   {max_dom}")
        print(f"Total AOD days:      {total_days}")

        # Process all domains specified by max_dom.
        for i in range(1, max_dom + 1):
            domain = f"d{i:02d}"
            update_aod(domain, start_date, end_date)

        print("\n" + "=" * 70)
        print("ALL DOMAINS PROCESSED SUCCESSFULLY")
        print("=" * 70)
        print("namelist.input was not modified.")
        print("MPTABLE.TBL was not modified.")

    except (
        FileNotFoundError,
        ValueError,
        OSError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"ERROR: {error}")
        raise SystemExit(1)

