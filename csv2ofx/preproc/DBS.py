import pandas as pd
import numpy as np
import re


def preprocess(folder, filename):
    path = f"{folder}/{filename}"
    new_path = f"{folder}/{filename.split('.')[0] + '_processed.csv'}"
    with open(path, "r") as myfile:
        data = myfile.readlines()
    myfile.close()
    data = [line.rstrip("\n") for line in data]
    for i in range(0, len(data)):
        print(data[i])
        if any(ext in data[i] for ext in ["AWL","POS"]):
            data[i] = data[i][:-1] # take off end comma for AWL transactions
        data[i] = data[i].replace(", ,",",,")
        data[i] = re.sub(r", +",",",data[i])
    with open(new_path, "w") as myfile:
        for line in data:
            myfile.write(line+"\n")
    myfile.close()

    a = pd.read_csv(new_path, skiprows=17, skip_blank_lines=True, error_bad_lines=False, index_col=False)
    a["Transaction Date"] = pd.to_datetime(a["Transaction Date"], format="%d %b %Y").dt.strftime("%Y-%m-%d")
    a["Amount"] = np.where(a["Debit Amount"].isna(), a["Credit Amount"], -a["Debit Amount"])
    a["Description"] = np.where(a["Transaction Ref1"].isna(), "", a["Transaction Ref1"])
    a["Notes"] = np.where(a["Transaction Ref2"].isna(), "", a["Transaction Ref2"]) + \
                 np.where(a["Transaction Ref3"].isna(), "", a["Transaction Ref3"])
    a = a[["Transaction Date", "Amount", "Description", "Notes"]]
    a.to_csv(new_path, index=False)
    return new_path
