# -*- coding: utf-8 -*-
# from odoo import http


# class RtChangeCurrencyRounding(http.Controller):
#     @http.route('/rt_change_currency_rounding/rt_change_currency_rounding/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/rt_change_currency_rounding/rt_change_currency_rounding/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('rt_change_currency_rounding.listing', {
#             'root': '/rt_change_currency_rounding/rt_change_currency_rounding',
#             'objects': http.request.env['rt_change_currency_rounding.rt_change_currency_rounding'].search([]),
#         })

#     @http.route('/rt_change_currency_rounding/rt_change_currency_rounding/objects/<model("rt_change_currency_rounding.rt_change_currency_rounding"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('rt_change_currency_rounding.object', {
#             'object': obj
#         })
