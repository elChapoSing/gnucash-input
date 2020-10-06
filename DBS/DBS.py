from __future__ import absolute_import, print_function
import re
import itertools as it
import pandas as pd
from datetime import datetime as dt
import csv

# csv2ofx
from meza.io import read_csv, IterStringIO
from csv2ofx import utils
from csv2ofx.ofx import OFX
from csv2ofx.preproc.DBS import preprocess

# pdfminer.six
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO

#environment stuff
from dotenv import load_dotenv
from os.path import join
from os import environ as env

load_dotenv(".env")
FIRST_NAME = env.get("FIRST_NAME")
LAST_NAME = env.get("LAST_NAME")
SPOUSE_NAME = env.get("SPOUSE_NAME")

def gen_ofx(input_path, output_path, is_credit=False):
    if is_credit:
        from csv2ofx.mappings.DBS_credit import mapping
    else:
        from csv2ofx.mappings.DBS import mapping
    ofx = OFX(mapping)
    records = read_csv(input_path)
    groups = ofx.gen_groups(records)
    trxns = ofx.gen_trxns(groups)
    cleaned_trxns = ofx.clean_trxns(trxns)
    data = utils.gen_data(cleaned_trxns)
    content = it.chain([ofx.header(), ofx.gen_body(data), ofx.footer()])
    with open(output_path, "w") as myfile:
        for line in IterStringIO(content):
            myfile.write(line.decode("utf-8"))


def preprocess_pdf(folder_path, filename):
    def convert_pdf_to_txt(path):
        rsrcmgr = PDFResourceManager()
        retstr = StringIO()
        codec = 'utf-8'
        laparams = LAParams()
        device = TextConverter(rsrcmgr, retstr, laparams=laparams)
        fp = open(path, 'rb')
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        password = ""
        maxpages = 0
        caching = True
        pagenos = set()
        for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password, caching=caching,
                                      check_extractable=True):
            interpreter.process_page(page)
        text = retstr.getvalue()
        fp.close()
        device.close()
        retstr.close()
        return text

    text = convert_pdf_to_txt("/".join([folder_path, filename]))
    text = text.splitlines()
    # replace multi spaces by one space + trim
    text = [re.sub(r" +", " ", line.strip()) for line in text if line != ""]
    # get rid of vertical text
    text = [line for line in text if len(line) > 1]
    # values cleanup
    regex_to_remove = [
        r"[0-9]+ of [0-9]+",  # page numbers
        r"SUB-TOTAL:"
    ]
    value_to_remove = [
        "Co. Reg. No. 196800306E",
        "GST Registration No: MR-8500180-3",
        "DBS Bank Ltd",
        "Orchard Road P.O.Box 360 S(912312)",
        "www.dbs.com",
        f"NEW TRANSACTIONS {SPOUSE_NAME}",
    ]
    regex_to_remove = [re.compile(regex) for regex in regex_to_remove]
    for regex in regex_to_remove:
        text = [line for line in text if not regex.match(line)]
    for value in value_to_remove:
        text = [line for line in text if not line == value]

    # select "interesting" data
    if f"NEW TRANSACTIONS {FIRST_NAME} {LAST_NAME}" in text:
        text = text[(text.index(f"NEW TRANSACTIONS {FIRST_NAME} {LAST_NAME}") + 1):(text.index("TOTAL:"))]
    else:
        text = text[(text.index(f"NEW TRANSACTIONS {LAST_NAME} {FIRST_NAME}") + 1):(text.index("TOTAL:"))]
    # write cleaned-up txt to drive
    output_folder = folder_path
    output_filename = "intermediate.txt"
    output_path = "/".join([output_folder, output_filename])
    with open(output_path, "w") as myfile:
        [myfile.write(line + "\n") for line in text]
    myfile.close()
    return output_folder, output_filename


def process_clean_txt(folder, filename, current_year):
    file_path = "/".join([folder, filename])
    with open(file_path, "r") as myfile:
        text = myfile.readlines()
    myfile.close()
    text = [line.rstrip("\n") for line in text]
    text_num = []
    text_str = []
    text_dte = []
    amount_regex = re.compile(r"[0-9,]+\.[0-9]{2}( CR)*")
    date_reg = re.compile(r"[0-9]{2} [A-Z]{3}")
    for line in text:
        a = date_reg.match(line)
        if a:
            if not len(line) == a.end() - a.start():
                raise AssertionError(
                    f"Extra characters in date row in {file_path}: {line}\nPlease Correct in the text file and rerun in '--level_from txt' mode.")
            text_dte.append(line)
        elif amount_regex.match(line):
            text_num.append(line)
        else:
            text_str.append(line)

    # clean numbers
    clean_num = text_num[2:]  # get rid of last month balance
    clean_num = [num.replace(",", "") for num in clean_num ]
    for i, num in enumerate(clean_num):
        if "CR" in num:
            clean_num[i] = float(num.replace("CR", ""))
        else:
            clean_num[i] = -float(num)
    all_num = True
    while all_num:
        subtotal_amount = input(
            "Please enter subtotal amounts (or 'done' if done): ")
        if subtotal_amount == "done":
            all_num = False
        else:
            clean_num = [num for num in clean_num if not abs(float(num)) == abs(float(subtotal_amount))]


    # clean descriptions
    currencies = ["DONG", "EUROPEAN MONETARY COOP FUND", "U. S. DOLLAR"]
    currencies_reg = [re.compile(x) for x in currencies]
    clean_str = []
    for i, txt in enumerate(text_str):
        if any([x.match(txt) for x in currencies_reg]):
            clean_str[len(clean_str)-1] = clean_str[len(clean_str)-1] + " " + txt
        else:
            clean_str.append(txt)

    # clean dates
    clean_dte = [dt.strptime(x, "%d %b").replace(year=current_year).strftime("%Y-%m-%d") for x in text_dte]

    if len({len(clean_dte), len(clean_str), len(clean_num)}) != 1:
        a = it.zip_longest(text_num, clean_num, text_dte, clean_dte, text_str, clean_str, fillvalue="NA")
        with open("./wrong_cleanups.csv", "w") as the_file:
            out = csv.writer(the_file)
            out.writerows(a)
        raise AssertionError("The cleanup did not go as expected, please check the individual files.")

    output_df = pd.DataFrame(columns=["Transaction Date", "Amount", "Description", "Notes"])
    output_df["Transaction Date"] = clean_dte
    output_df["Amount"] = clean_num
    output_df["Description"] = clean_str
    output_df["Notes"] = ""
    output_folder = folder
    output_filename = "output.csv"
    output_path = "/".join([output_folder, output_filename])
    output_df.to_csv(output_path, index=False)
    return output_folder, output_filename


def process(filename, type, level_from, current_year):
    print(filename)
    print("process DBS files")
    is_credit = False
    if type == "checking":
        new_path = preprocess("./DBS/Input", filename)
        gen_ofx(new_path, "./DBS/Output/output_checking.ofx")
    elif type == "credit":
        is_credit = True
        if level_from == "pdf":
            txt_folder, txt_filename = preprocess_pdf("./DBS/Input", filename)
        else:
            txt_folder, txt_filename = "./DBS/Input", filename
        if level_from == "txt" or level_from == "pdf":
            csv_folder, csv_filename = process_clean_txt(txt_folder, txt_filename, current_year)
        else:
            csv_folder, csv_filename = "./DBS/Input", filename

        gen_ofx("/".join([csv_folder, csv_filename]), "./DBS/Output/output_credit.ofx", is_credit=is_credit)
    else:
        raise ValueError(f"Unknown type for DBS: {type}.")


if __name__ == '__main__':
    print("nothing to do")
