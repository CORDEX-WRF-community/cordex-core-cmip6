#!/usr/bin/env python3
# =============================================================================
# Update MPTABLE.TBL
#
# WHY IS THIS UPDATE NECESSARY?
#
# WRF uses the CO2 partial pressure in MPTABLE.TBL for radiation
# calculations. The CO2 value should correspond to the simulation's
# start year so that radiation calculations use the appropriate
# greenhouse gas concentration.
#
# This routine reads start_year from namelist.input, retrieves the
# corresponding CO2 value from CAMtr_volume_mixing_ratio, and updates
# the CO2 entry in MPTABLE.TBL.
#
# Original:
#    https://github.com/CORDEX-WRF-community/euro-cordex-cmip6/blob/main/util/update_and_restart.py
#
# Contact: milovacj@unican.es
# Original created: [03-12-2023]
# Updated: [16-10-2026]
# =============================================================================


from pathlib import Path
import re

# =============================================================================
# Configuration
# =============================================================================

NAMELIST = Path("./namelist.input")
GHG_FILE = Path("./CAMtr_volume_mixing_ratio")
MPTABLE = Path("./MPTABLE.TBL")
TARGET_STRING = "!co2 partial pressure" # The strin that appears in MPTABLE

# =============================================================================
# Read the simulation start year from namelist.input
# =============================================================================

def get_start_year():
    """Read start_year from namelist.input."""

    pattern = re.compile(r"^\s*start_year\s*=\s*(\d+)", re.IGNORECASE)

    if not NAMELIST.exists():
        raise FileNotFoundError(f"Cannot find {NAMELIST}")

    with open(NAMELIST, "r") as file:
        for line in file:
            line = line.split("!", 1)[0].strip()

            if not line or line.startswith("#"):
                continue

            match = pattern.match(line)
            if match:
                return int(match.group(1))

    raise ValueError("start_year was not found in namelist.input")


# =============================================================================
# Read the CO2 value for the simulation start year
# =============================================================================

def get_co2_value(start_year):
    """Read the CO2 mixing ratio for the requested year."""

    if not GHG_FILE.exists():
        raise FileNotFoundError(f"Cannot find {GHG_FILE}")

    with open(GHG_FILE, "r") as file:
        for line in file:
            line = line.split("!", 1)[0].strip()

            if not line:
                continue

            fields = line.split()

            if len(fields) >= 2:
                try:
                    year = int(fields[0])
                except ValueError:
                    continue

                if year == start_year:
                    return fields[1]

    raise ValueError(
        f"CO2 value for year {start_year} was not found in {GHG_FILE}")


def update_mptable():
    """Update the CO2 entry in MPTABLE.TBL."""

    start_year = get_start_year()
    co2_value = get_co2_value(start_year)

    if not MPTABLE.exists():
        raise FileNotFoundError(f"Cannot find {MPTABLE}")

    with open(MPTABLE, "r") as file:
        lines = file.readlines()

    # Match CO2= or CO2 = on the same line.
    pattern = re.compile(r"\bCO2 ?=", re.IGNORECASE)

    matching_lines = [
        i for i, line in enumerate(lines)
        if pattern.search(line) ]

    if not matching_lines:
        raise ValueError(
            "No line containing 'CO2=' or 'CO2 =' was found in MPTABLE.TBL" )

    if len(matching_lines) > 1:
        raise ValueError(
            "Multiple CO2 entries were found in MPTABLE.TBL; "
            "no changes were made." )

    index = matching_lines[0]

    # Update the CO2 value and use TARGET_STRING as the comment.
    lines[index] = f"  CO2 = {co2_value}e-06 {TARGET_STRING}\n"

    with open(MPTABLE, "w") as file:
        file.writelines(lines)

    print(f"Simulation start year: {start_year}")
    print(f"CO2 value: {co2_value}e-06")
    print(f"Updated {MPTABLE}")


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    update_mptable()
