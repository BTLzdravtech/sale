import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr

    _logger.info("START add with_returns to sale_order")
    openupgrade.add_columns(env, [
        ("sale_order", "with_returns", "boolean"),
    ])
    _logger.info("END add with_returns to sale_order")


    _logger.info("START update delivery_status selection field in sale_order_line")
    openupgrade.add_columns(env, [
        ("sale.order.line", "delivery_status", "selection"),
    ])
    _logger.info("END update delivery_status selection field in sale_order_line")