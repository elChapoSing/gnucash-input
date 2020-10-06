import os
import sys
import argparse
import logging
from datetime import datetime as dt
from CA import CA
from DBS import DBS

sys.path.append("D:/Projects/gnucash-input")

my_logger = logging.getLogger('Files Processing')
my_logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
my_logger.addHandler(console_handler)

def str2bool(str):
    if str.upper()[0] == "T":
        return True
    elif str.upper()[0] == "F":
        return False
    else:
        return None


parser = argparse.ArgumentParser(description="", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('--source', required=True, default=None, help="source to run")
parser.add_argument('--type', required=True, default="checking", help="type of the source (e.g checking, credit)")
parser.add_argument('--level_from', required=False, default="pdf", help="run dbs credit from which level ? pdf or txt")
parser.add_argument('--current_year', required=False, default=dt.today().year, type=int,
                    help="the year of the dates for the credit card pdf")
parser.add_argument('--filename', required=True, default=None, help="filename")

if __name__ == '__main__':

    args = parser.parse_args()
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    my_logger.debug(str(args))

    if args.source == "DBS":
        DBS.process(filename=args.filename, type=args.type, level_from=args.level_from,current_year=args.current_year)
