##############################################################################
#
#    Copyright (C) 2015  ADHOC SA  (http://www.adhoc.com.ar)
#    All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Sale Exception Credit Limit',
    'version': "17.0.1.0.0",
    'author': 'ADHOC SA',
    'website': 'www.adhoc.com.ar',
    'license': 'AGPL-3',
    'depends': [
        'sale_exception',
        'sale_exceptions_ignore_approve',
    ],
    'data': [
        'security/sale_exception_credit_limit_security.xml',
        'data/exception_rule_data.xml',
        'views/res_partner_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'demo': [
        'demo/res_partner_demo.xml'
    ],
    'installable': True,
    'post_init_hook': '_post_init_credit',
}
