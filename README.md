# gnucash-input
This script generates OFX file to be imported into any accounting software (we use [GnuCash](https://www.gnucash.org/)) from DBS credit card PDF statements or checking account CSV files.


Before running the script, make sure to have the `.env` file properly setup (see `example.env` in the repo)

**To process the pdf statement for a DBS credit card :**

>python main.py --source DBS --type credit --filename input.pdf 

where `input.pdf` is in the `DBS/input` folder 

**To process the csv file  for a DBS checking account :**

>python main.py --source DBS --type checking --filename input.csv

where `input.csv` is in the `DBS/input` folder

The output files will be named `output_checking.ofx` and `output_credit.ofx` in the `DBS/Output` folder.

