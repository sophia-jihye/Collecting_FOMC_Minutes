# Collecting FOMC Minutes

* Reference
    - Scraping: https://github.com/tengtengtengteng/Webscraping-FOMC-Statements
    - Data source: https://www.federalreserve.gov/monetarypolicy/materials/

## Command line
```
python main_scrape.py --start_mmddyyyy "01/01/1990" --end_mmddyyyy "01/25/2023"
```

### Input
| Variable           | Type | Example                                                             |
| :----------------- | :--- | :------------------------------------------------------------------ |
| start\_mmddyyyy    | str  | "01/01/1990"                                                        |
| end\_mmddyyyy      | str  | "01/25/2023"                                                        |
| selenium\_filepath | str  | "C:\\GIT\\SELENIUM\_DRIVERS\\chromedriver\_win32\\chromedriver.exe" |
| save\_root\_dir    | str  | "./Minutes"                                                      |

### Output 
* One text file contains information regarding a meeting date, document date, and document.
* The following shows the directory structure where the scraped and processed documents are stored.
```
├── main_scrape.py
├── Minutes
│   ├── raw
│        ├── 1993
│             ├── 19940326.txt  # The filename indicates the date that the statements was uploaded on the website. `document_date`
│             │					# The first line of the file indicates the date the meeting was held. `meeting_date`
│             │					# The remainder of the file is the FOMC statement. `document`
│             ├── 19930521.txt
│             ├── ...
│        ├── 1994
│             ├── 19940204.txt
│             ├── ...
│        ├── ...
```

* Example of raw documents (raw/2023/20230104.txt)
```
1. The Federal Open Market Committee is referenced as the "FOMC" and the "Committee" in these minutes; the Board of Governors of the Federal Reserve System is referenced as the "Board" in these minutes. Return to text 2. Attended through the discussion of developments in financial markets and open market operations. Return to text 3. Attended Tuesday's session only.
```

## Error Handling
* If an error occurs, the case is saved in the `Minutes/raw/errors.csv` file.
* After checking this file, handle the errors one by one.
  - `Scrape_items_in_errors.csv.ipynb`

*****

# Preprocessing (Work In Progress)

* Related file: `Numbered_list_removal.ipynb`

* Example of processed documents (no-numbered-list/2023/20230104.txt)
```
Federal Open Market Committee is referenced as the "FOMC" and the "Committee" in these minutes; the Board of Governors of the Federal Reserve System is referenced as the "Board" in these minutes. Return to text  Attended through the discussion of developments in financial markets and open market operations. Return to text  Attended Tuesday's session only. Return to text  Attended opening remarks for Tuesday's session only. 
```
