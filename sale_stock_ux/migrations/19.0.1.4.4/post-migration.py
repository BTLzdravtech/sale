from odoo import SUPERUSER_ID, api

BATCH_SIZE = 1000


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _recompute_in_batches(env, "sale.order", "with_returns")
    _recompute_in_batches(env, "sale.order.line", "delivery_status")


def _recompute_in_batches(env, model_name, field_name):
    records_model = env[model_name].with_context(active_test=False)
    last_id = 0
    while records := records_model.search([("id", ">", last_id)], order="id", limit=BATCH_SIZE):
        last_id = records[-1].id
        env.add_to_compute(records._fields[field_name], records)
        records._recompute_recordset([field_name])
        env.cr.commit()
