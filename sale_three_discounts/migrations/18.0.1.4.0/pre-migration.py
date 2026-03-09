import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr

    _logger.info("START add discount field to account_move_line")
    openupgrade.add_columns(env, [
        ("account_move_line", "discount", "float"),
    ])
    _logger.info("END add discount field to account_move_line")


    _logger.info("START add discount1 field to sale_order_line")
    openupgrade.add_columns(env, [
        ("sale_order_line", "discount1", "float"),
    ])
    _logger.info("END add discount1 field to sale_order_line")

    _logger.info("START add discount2 field to sale_order_line")
    openupgrade.add_columns(env, [
        ("sale_order_line", "discount2", "float"),
    ])
    _logger.info("END add discount2 field to sale_order_line")

    _logger.info("START add discount3 field to sale_order_line")
    openupgrade.add_columns(env, [
        ("sale_order_line", "discount3", "float"),
    ])
    _logger.info("END add discount3 field to sale_order_line")
