#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.pool import Pool
from .invoice import *

def register():
    Pool.register(
        InInvoicetoDraftStart,
        module='nodux_in_invoice2draft', type_='model')
    Pool.register(
        InInvoicetoDraft,
        module='nodux_in_invoice2draft', type_='wizard')
