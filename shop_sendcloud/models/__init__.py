# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _
from shop.money.fields import MoneyField
from shop.models.customer import BaseCustomer


class ShippingMethod(models.Model):
    id = models.PositiveIntegerField(primary_key=True)

    name = models.CharField(
        max_length=255,
    )

    carrier = models.CharField(
        max_length=32,
    )

    min_weight = models.DecimalField(
        max_digits=6,
        decimal_places=3,
    )

    max_weight = models.DecimalField(
        max_digits=8,
        decimal_places=3,
    )

    updated_at = models.DateTimeField(
        _("Updated at"),
        auto_now=True,
    )

    class Meta:
        verbose_name = _("Shipping Method")
        verbose_name_plural = _("Shipping Methods")


class ShippingDestination(models.Model):
    shipping_method = models.ForeignKey(
        ShippingMethod,
        related_name='destinations',
    )

    country = models.CharField(max_length=3)

    price = MoneyField(currency='EUR')

    class Meta:
        verbose_name = _("Shipping Destination")
        verbose_name_plural = _("Shipping Destination")
        unique_together = ['country', 'shipping_method']
