#!/bin/bash -l
#
# ============================================================
# ERA5 Data Download Script (SLURM job)
# ============================================================
#
# This script downloads ERA5 reanalysis data for WRF simuations
# (surface & pressure-level) for a selected domain and time period.
#
# It is designed to run on an HPC system using SLURM.
#
# -------------------------
# Usage:
# -------------------------
# sbatch script.sh YEAR MONTH DOMAIN
#
# Example:
# sbatch script.sh 2024 8 EAS
#
# -------------------------
# Inputs:
# -------------------------
# YEAR   - Year (e.g., 2024)
# MONTH  - Month (1–12)
# DOMAIN - Region identifier:
#          SAM (South America)
#          EAS (East Asia)
#          WAS (West Asia)
#          EUR (Europe)
#          AFR (Africa)
#
# -------------------------
# What the script does:
# -------------------------
# 1. Defines geographic bounds based on DOMAIN
# 2. Modifies ERA5 download Python templates using sed
# 3. Runs the generated Python scripts
# 4. Downloads:
#      - Surface data (sl)
#      - Pressure-level data (pl)
# 5. Stores output in:
#      ./data/DOMAIN/YEAR/
#
# Output files:
#   ERA5-YYYYMM-sl.grib
#   ERA5-YYYYMM-pl.grib
#
# ============================================================

#SBATCH --job-name=ERA5
#SBATCH --output=ERA5%j.out
#SBATCH --error=ERA5%j.error
#SBATCH --ntasks=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=72:00:00
#SBATCH --cpus-per-task=1              
#SBATCH --threads-per-core=1

# -------------------------
# Directory setup
# -------------------------
CODEDIR="$PWD"
DATADIR="./data"
mkdir -p "$DATADIR"

# -------------------------
# Read arguments
# -------------------------
YEAR=$1    										# read year
MONTH=$(printf "%02d" "$2")   # read month
DOMAIN="${3^^}"   						# force uppercase, currently available domains (SAM, EAS, WAS, EUR, AFR)

MONTH_NONZERO=$((10#$MONTH))

# -------------------------
# Domain definition
# -------------------------
case "$DOMAIN" in
  SAM) North=25; South=-70; West=-120; East=-5 ;;
  EAS) North=70; South=-10; West=40;   East=200 ;;
  WAS) North=55; South=15;  West=5;    East=130 ;;
  EUR) North=90; South=0;   West=-50;  East=70 ;;
  AFR) North=50; South=-60; West=-40;  East=70 ;;
  *)
    echo "Unknown domain: $DOMAIN" >&2
    exit 1
    ;;
esac
echo "$DOMAIN -> N=$North S=$South W=$West E=$East"

# -------------------------
# Download function
# -------------------------
run_download () {
  local template=$1
  local type=$2
  local outfile="GetERA5-${YEAR}${MONTH}-${type}.py"

  sed \
    -e "s/YEAR/${YEAR}/g" \
    -e "s/MONTH/${MONTH_NONZERO}/g" \
    -e "s/North/${North}/g" \
    -e "s/West/${West}/g" \
    -e "s/South/${South}/g" \
    -e "s/East/${East}/g" \
    "$template" > "$outfile"

  python "$outfile"
  rm "$outfile"
}

# -------------------------
# Run downloads
# -------------------------
run_download "GetERA5-sl.py" "sl"
run_download "GetERA5-pl.py" "pl"

# -------------------------
# Move outputs
# -------------------------
OUTDIR="${DATADIR}/${DOMAIN}/${YEAR}"
mkdir -p "$OUTDIR"

mv "ERA5-${YEAR}${MONTH}-sl.grib" \
   "ERA5-${YEAR}${MONTH}-pl.grib" \
   "$OUTDIR/"

echo "Data stored in $OUTDIR"

exit 0
