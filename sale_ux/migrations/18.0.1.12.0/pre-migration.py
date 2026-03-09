import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr

    _logger.info("START add commercial_partner_id to sale.order")
    openupgrade.add_columns(env, [
        ("sale.order", "commercial_partner_id", "many2one"),
    ])

    openupgrade.logged_query(cr, """
        UPDATE sale_order so
           SET commercial_partner_id = rp.commercial_partner_id
          FROM res_partner rp
         WHERE so.partner_id = rp.id
           AND so.commercial_partner_id IS NULL
           AND rp.commercial_partner_id IS NOT NULL
    """)
    _logger.info("END add commercial_partner_id to sale.order")