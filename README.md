# Lotto results

Downloads the UK Lotto results after each Saturday draw and saves them to
`data/lotto.csv`. The Linthorpe Academicals club lottery Google Sheet reads that file.

- Runs automatically on Saturday night, with backups late Saturday and Sunday morning.
- To run it now: **Actions → Fetch Lotto results → Run workflow**.
- If a run fails, GitHub emails you. The sheet keeps working, and you can type
  the numbers into its Draws tab by hand.
