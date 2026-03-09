import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr


    _logger.info("START add gathering_balance to sale_order")
    openupgrade.add_columns(env, [
        ("sale_order", "gathering_balance", "float"),
    ])
    _logger.info("END add gathering_balance to sale_order")