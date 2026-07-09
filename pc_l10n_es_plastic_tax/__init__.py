# -*- coding: utf-8 -*-
from . import models
from . import wizard


def post_init_hook(env):
    # El peso técnico (p.ej. un tapón ~2 g) necesita más de 2 decimales para el
    # cálculo de kg desde el peso. Elevar la precisión de "Stock Weight" a 6.
    prec = env['decimal.precision'].search([('name', '=', 'Stock Weight')], limit=1)
    if prec and prec.digits < 6:
        prec.digits = 6
