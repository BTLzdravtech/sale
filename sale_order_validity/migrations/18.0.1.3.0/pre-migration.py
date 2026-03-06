import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr

    _logger.info("START add validity_days to sale_order")
    openupgrade.add_columns(env, [
        ("sale_order", "validity_days", "integer"),
    ])
    _logger.info("END add validity_days to sale_order")