from odoo import models, fields, api, _
from odoo.exceptions import Warning
from odoo.exceptions import UserError

class SentInvoiceEtaWiz(models.TransientModel):
    _name = 'sent.invoice.eta.wiz'
    _description = 'Sent Multiple Invoice Eta From Wizard'

    def sent_invoice_eta(self):
        signed_inovice = 0
        
        for rec in self.env['account.move'].browse(self._context.get('active_ids', [])):
            if rec.state in ('posted') and rec.eta_sign != True:
                rec.write({'eta_sign':True})
                rec.env.cr.commit()
            elif rec.state in ('draft'):
                rec.action_post()
                rec.write({'eta_sign':True})
                rec.env.cr.commit()
            
            if rec.is_signed != True or rec.eta_status not in ('submitted', 'valid'):
                signed_inovice = signed_inovice + 1
        
        if signed_inovice > 0:
            raise UserError("Your invoices has not been signed yet") 

        return
