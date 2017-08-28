# -*- coding: utf-8 -*-

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
import psycopg2
from decimal import Decimal
import StringIO
from trytond.pyson import Eval
from trytond.model import ModelSQL, Workflow, fields, ModelView
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta
from trytond.wizard import Wizard, StateAction, StateView, StateTransition, \
    Button
__all__ = ['InInvoicetoDraftStart', 'InInvoicetoDraft']
__metaclass__ = PoolMeta

class Invoice():
    'Invoice'
    __name__ = 'account.invoice'


class InInvoicetoDraftStart(ModelView):
    'In Invoice to Draft Start'
    __name__ = 'nodux.account.in.invoice.to.draft.start'


class InInvoicetoDraft(Wizard):
    'In Invoice To Draft'
    __name__ = 'nodux.account.in.invoice.to.draft'

    start = StateView('nodux.account.in.invoice.to.draft.start',
        'nodux_in_invoice2draft.in_invoice_to_draft_start_view_form', [
        Button('Cancel', 'end', 'tryton-cancel'),
        Button('Draft', 'draft_', 'tryton-ok', default=True),
        ])
    draft_ = StateAction('account_invoice.act_invoice_form')
    #accept = StateTransition()

    def do_draft_(self, action):
        pool = Pool()
        Sale = pool.get('sale.sale')
        Invoice = pool.get('account.invoice')
        Withholding = pool.get('account.withholding')
        VoucherLine = pool.get('account.voucher.line')
        invoices = Invoice.browse(Transaction().context['active_ids'])
        ModelData = pool.get('ir.model.data')
        User = pool.get('res.user')
        Group = pool.get('res.group')
        for invoice in invoices:
            cursor = Transaction().cursor
            def in_group():
                origin = str(invoice)
                group = Group(ModelData.get_id('nodux_in_invoice2draft',
                        'group_in_invoice_draft'))
                transaction = Transaction()

                user_id = transaction.user
                if user_id == 0:
                    user_id = transaction.context.get('user', user_id)
                if user_id == 0:
                    return True
                user = User(user_id)
                return origin and group in user.groups

            if not in_group():
                self.raise_user_error('No tiene permiso para modificar la factura %s', invoice.number)
            else:
                if invoice.type == "in_invoice":

                    if invoice.ref_withholding != "":
                        withholdings = Withholding.search([('number','=', invoice.ref_withholding)])
                        if withholdings:
                            for withholding in withholdings:
                                # cursor.execute('DELETE FROM account_withholding_tax WHERE withholding = %s' %withholding.id)
                                # cursor.execute('DELETE FROM account_withholding WHERE id =%s' %withholding.id)
                                withholding.state = "annulled"
                                withholding.save()

                    if invoice.move:
                        cursor.execute('DELETE FROM account_move_line WHERE move = %s' %invoice.move.id)
                        cursor.execute('DELETE FROM account_move WHERE id = %s' %invoice.move.id)
                    #for line in invoice.lines:
                        #cursor.execute('DELETE FROM account_invoice_line WHERE id = %s' %line.id)
                    #cursor.execute('DELETE FROM account_invoice WHERE id = %s' %invoice.id)
                    if invoice.state == 'paid':
                        voucher_line = VoucherLine.search([('name','=', invoice.number)])
                        cursor.execute('DELETE FROM account_voucher_line WHERE name =%s' %invoice.number)
                        cursor.execute('DELETE FROM account_voucher WHERE ud =%s' %voucher_line.voucher)
                        cursor.execute('DELETE FROM account_move_line WHERE move = %s' %voucher_line.voucher.move.id)
                        cursor.execute('DELETE FROM account_move WHERE id = %s' %voucher_line.voucher.move.id)
                    invoice.number = None
                    invoice.state = "draft"
                    invoice.move = None
                    invoice.ref_withholding = None
                    invoice.save()
                else:
                    self.raise_user_error('No puede modificar una factura de venta. Dirijase a Ventas->Ventas TPV')
