# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.template.loader import get_template
from django.utils.translation import ugettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from shop.models.customer import BaseCustomer


class Customer(BaseCustomer):
    SALUTATION = [('mrs', _("Mrs.")), ('mr', _("Mr.")), ('na', _("(n/a)"))]

    number = models.PositiveIntegerField(
        _("Customer Number"),
        null=True,
        default=None,
        unique=True,
    )

    salutation = models.CharField(
        _("Salutation"),
        max_length=5,
        choices=SALUTATION,
    )

    phone_number = PhoneNumberField(
        _("Phone number"),
        blank=True,
        null=True,
    )

    def get_number(self):
        return self.number

    def get_or_assign_number(self):
        if self.number is None:
            aggr = Customer.objects.filter(number__isnull=False).aggregate(models.Max('number'))
            self.number = (aggr['number__max'] or 0) + 1
            self.save()
        return self.get_number()

    @classmethod
    def reorder_form_fields(self, field_order):
        field_order.insert(0, 'salutation')
        field_order.append('phone_number')
        return field_order

    def as_text(self):
        template = get_template('shop_sendcloud/customer.txt')
        return template.render({'customer': self})
