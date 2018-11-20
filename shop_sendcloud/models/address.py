# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.template.loader import get_template
from django.utils.translation import ugettext_lazy as _
from shop.models.address import BaseShippingAddress, BaseBillingAddress, CountryField


class AddressModelMixin(models.Model):
    """
    SendCloud prescribes an address model, which differs slightly from django-SHOP's default address model.
    Add this model to the merchant's ``model.py``, if ``shop_sendcloud`` is used as your delivery provider.
    """
    name = models.CharField(
        _("Full name"),
        max_length=1024,
    )

    company_name = models.CharField(
        _("Company name"),
        max_length=1024,
        blank=True,
        null=True,
    )

    address = models.CharField(
        _("Address line"),
        max_length=1024,
    )

    house_number = models.CharField(
        _("House number"),
        max_length=12,
    )

    postal_code = models.CharField(
        _("ZIP / Postal code"),
        max_length=12,
    )

    city = models.CharField(
        _("City"),
        max_length=1024,
    )

    country = CountryField(_("Country"))

    class Meta:
        abstract = True


class ShippingAddress(BaseShippingAddress, AddressModelMixin):
    class Meta:
        verbose_name = _("Shipping Address")
        verbose_name_plural = _("Shipping Addresses")

    def as_text(self):
        template = get_template('shop_sendcloud/address.txt')
        return template.render({'address': self})


class BillingAddress(BaseBillingAddress, AddressModelMixin):
    class Meta:
        verbose_name = _("Billing Address")
        verbose_name_plural = _("Billing Addresses")

    def as_text(self):
        template = get_template('shop_sendcloud/address.txt')
        return template.render({'address': self})
