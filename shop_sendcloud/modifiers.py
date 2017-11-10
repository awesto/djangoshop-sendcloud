# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from decimal import Decimal

from django.db.utils import OperationalError
from django.utils.translation import ugettext_lazy as _

from shop.modifiers.pool import cart_modifiers_pool
from shop.serializers.cart import ExtraCartRow
from shop.shipping.modifiers import ShippingModifier
from shop.money import MoneyMaker

from shop_sendcloud.models import ShippingMethod, ShippingDestination

EUR = MoneyMaker('EUR')  # at SendCloud, everything is charged in Euros


class SendcloudShippingModifierBase(ShippingModifier):
    carrier = None

    def get_queryset(self):
        return ShippingMethod.objects.filter(carrier=self.carrier)

    def get_choice(self):
        qs = self.get_queryset().order_by('id')
        return (self.identifier, qs.first().name)

    def add_extra_cart_row(self, cart, request):
        if not self.is_active(cart) and len(cart_modifiers_pool.get_shipping_modifiers()) > 1:
            return

        destinations = ShippingDestination.objects.filter(
            shipping_method__carrier=self.carrier,
            country=cart.shipping_address.country,
            shipping_method__min_weight__lte=cart.weight,
            shipping_method__max_weight__gte=cart.weight,
        ).order_by('price')
        if destinations:
            destination = destinations.first()
            parcel = self.get_sendcloud_parcel(cart)
            parcel['shipment'] = {'id': destination.shipping_method_id}
            cart.extra['sendcloud_data'] = {'parcel': parcel}
            amount = EUR(destination.price)
            instance = {'label': _("Shipping costs"), 'amount': amount}
            cart.extra_rows[self.identifier] = ExtraCartRow(instance)
            cart.total += amount
        else:
            instance = {'label': _("Unable to ship"), 'amount': EUR()}
            cart.extra_rows[self.identifier] = ExtraCartRow(instance)

    def get_sendcloud_parcel(self, cart):
        shipping_address = cart.shipping_address or cart.billing_address
        data = {
            'name': shipping_address.name,
            'address': shipping_address.address,
            'house_number': shipping_address.house_number,
            'city': shipping_address.city,
            'postal_code': shipping_address.postal_code,
            'email': cart.customer.email,
            'country': shipping_address.country,
            'weight': str(cart.weight.quantize(Decimal('0.000'))),
            'insured_value': int(cart.subtotal),
        }
        if shipping_address.company_name:
            data['company_name'] = shipping_address.company_name
        if cart.customer.phone_number:
            data['telephone'] = str(cart.customer.phone_number)
        return data

class SendcloudShippingModifiers(list):
    """
    A list of possible shipping modifiers for this provider
    """
    def __init__(self):
        try:
            ShippingMethod.objects.exists()
        except OperationalError:
            return  # in case the table does not exist yet
        for carrier, in ShippingMethod.objects.values_list('carrier').distinct():
            name = 'Sendcloud{}Modifier'.format(carrier.title())
            attrs = {
                'carrier': carrier,
                'identifier': 'sendcloud:{}'.format(carrier),
            }
            self.append(type(str(name), (SendcloudShippingModifierBase,), attrs))
