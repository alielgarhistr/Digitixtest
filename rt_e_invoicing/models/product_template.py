# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class ProductTemplate(models.Model):
    _inherit = "product.template"

    eta_code_type = fields.Selection([('GS1', 'GS1'), ('EGS', 'EGS')],
                                     string='ETA Code Type',
                                     default='GS1',
                                     compute='_compute_eta_code_type',
                                     inverse='_set_eta_code_type', store=True)

    gpc_code = fields.Char(
        'GPC Code',
        compute='_compute_gpc_code',
        inverse='_set_gpc_code', store=True)

    @api.depends('product_variant_ids', 'product_variant_ids.eta_code_type')
    def _compute_eta_code_type(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.eta_code_type = template.product_variant_ids.eta_code_type
        for template in (self - unique_variants):
            template.eta_code_type = False

    def _set_eta_code_type(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.eta_code_type = self.eta_code_type

    @api.depends('product_variant_ids', 'product_variant_ids.gpc_code')
    def _compute_gpc_code(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.gpc_code = template.product_variant_ids.gpc_code
        for template in (self - unique_variants):
            template.gpc_code = False

    def _set_gpc_code(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.gpc_code = self.gpc_code

    # override
    @api.model_create_multi
    def create(self, vals_list):
        ''' Store the initial standard price in order to be able to retrieve the cost of a product template for a given date'''
        templates = super(ProductTemplate, self).create(vals_list)
        if "create_product_product" not in self._context:
            templates._create_variant_ids()

        # This is needed to set given values to first variant after creation
        for template, vals in zip(templates, vals_list):
            related_vals = {}
            if vals.get('barcode'):
                related_vals['barcode'] = vals['barcode']
            if vals.get('default_code'):
                related_vals['default_code'] = vals['default_code']
            if vals.get('standard_price'):
                related_vals['standard_price'] = vals['standard_price']
            if vals.get('volume'):
                related_vals['volume'] = vals['volume']
            if vals.get('weight'):
                related_vals['weight'] = vals['weight']
            # Please do forward port
            if vals.get('packaging_ids'):
                related_vals['packaging_ids'] = vals['packaging_ids']
            if vals.get('gpc_code'):
                related_vals['gpc_code'] = vals['gpc_code']
            if related_vals:
                template.write(related_vals)

        return templates