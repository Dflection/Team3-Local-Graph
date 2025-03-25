# **DEPRECATED, TIMES NOW CALCULATED WITHIN EXCEL SPREADSHEET**

# Naismith's Rule Travel Time Calculator

This project calculates estimated travel times for hiking or travel routes using Naismith's Rule. It reads elevation gain, elevation loss, and distance data from an Excel file (`data.xlsx`) and outputs calculated travel times back into the same file.

## Files

*   **`calculate_time.py`**
    *   **Purpose:** Main script. Calculates travel times using Naismith's Rule and coordinates the data reading and writing processes.
    *   **Usage:** Run this script to perform the calculations.
    *   **Dependencies:** `read_xlsx.py`, `write_xlsx.py`, `openpyxl`, `data.xlsx`
*   **`read_xlsx.py`**
    *   **Purpose:** Reads data (elevation gain, loss, distance) from multiple sheets in `data.xlsx` and returns it as a dictionary.
    *   **Usage:** Called by `calculate_time.py`.
    *   **Dependencies:** `openpyxl`
*   **`write_xlsx.py`**
    *   **Purpose:** Writes calculated travel times to a new sheet ("Time") in `data.xlsx`, using cell addresses as keys.
    *   **Usage:** Called by `calculate_time.py`.
    *   **Dependencies:** `openpyxl`

## How to Use

1.  **Install:** `pip install openpyxl`
2.  **Prepare `data.xlsx`:**
    *   Create an Excel file named `data.xlsx`.
    *   Include at least three sheets with corresponding data in the same cell addresses across each sheet.
    *   Data must start in row 2, column 2.
3.  **Run:** `python calculate_time.py`
4.  **Check Results:** Open `data.xlsx` and view the calculated times in the new "Time" sheet.

## Important Notes

*   Naismith's Rule provides an *estimate*. Actual travel times may vary.
*   Ensure `data.xlsx`, `calculate_time.py`, `read_xlsx.py`, and `write_xlsx.py` are all in the same folder.
* The data from each sheet in `data.xlsx` should be in the same cell address.

## Future Development

* Consider how to import data from Caltopo into the first 3 sheets of `data.xlsx`.

