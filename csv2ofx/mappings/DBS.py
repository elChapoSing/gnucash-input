from __future__ import (
    absolute_import, division, print_function, unicode_literals)

from operator import itemgetter

mapping = {
    'has_header': True,
    'is_split': False,
    'bank': 'DBS',
    'currency': 'SGD',
    'delimiter': ',',
    'account': "DBS Checking",
    'date': itemgetter('Transaction Date'),
    'amount': itemgetter('Amount'), #to create
    'desc': itemgetter('Description'), #to create
    'notes': itemgetter('Notes'), #to create
}
