# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from decimal import Decimal
import math
import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db.utils import OperationalError, ProgrammingError
from django.utils.translation import ugettext_lazy as _
from shop.modifiers.pool import cart_modifiers_pool
from shop.serializers.cart import ExtraCartRow
from shop.shipping.modifiers import ShippingModifier
from shop.money import MoneyMaker
from shop_sendcloud.models import ShippingMethod, ShippingDestination

EUR = MoneyMaker('EUR')  # at SendCloud, everything is charged in Euros


class SendcloudShippingModifierBase(ShippingModifier):
    carrier = None
    create_parcel_url = 'https://panel.sendcloud.sc/api/v2/parcels/'
    cancel_parcel_url = 'https://panel.sendcloud.sc/api/v2/parcels/{}/cancel'
    credentials = settings.SHOP_SENDCLOUD['API_KEY'], settings.SHOP_SENDCLOUD['API_SECRET']
    error_message = _("Parcel can not be delivered: {}")

    def get_queryset(self):
        return ShippingMethod.objects.filter(carrier=self.carrier)

    def get_choice(self):
        qs = self.get_queryset().order_by('id')
        return (self.identifier, qs.first().name)

    def add_extra_cart_row(self, cart, request):
        if not self.is_active(cart) and len(cart_modifiers_pool.get_shipping_modifiers()) > 1:
            return

        weight = max(cart.weight, Decimal('0.001')).quantize(Decimal('0.000'))
        cheapest_destination = ShippingDestination.objects.filter(
            shipping_method__carrier=self.carrier,
            country=cart.shipping_address.country if cart.shipping_address else None,
            shipping_method__min_weight__lte=weight,
            shipping_method__max_weight__gte=weight,
        ).order_by('price').first()
        if cheapest_destination:
            parcel = self.get_sendcloud_parcel(cart)
            parcel.update(
                shipment={'id': cheapest_destination.shipping_method_id},
                weight=str(weight),
            )
            cart.extra['sendcloud_data'] = {'parcel': parcel}
            amount = EUR(cheapest_destination.price)
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
            'insured_value': math.ceil(cart.subtotal / 100) * 100,
        }
        if shipping_address.company_name:
            data['company_name'] = shipping_address.company_name
        if cart.customer.phone_number:
            data['telephone'] = str(cart.customer.phone_number)
        return data

    def ship_the_goods(self, delivery):
        if not delivery.order.associate_with_delivery:
            msg = "Either add 'shop.shipping.workflows.PartialDeliveryWorkflowMixin' or \n" \
                  "  'shop.shipping.workflows.CommissionGoodsWorkflowMixin' to settings.SHOP_ORDER_WORKFLOWS"
            raise ImproperlyConfigured(msg)
        carrier = delivery.order.extra['shipping_modifier'][len('sendcloud:'):]
        destination_country = delivery.order.extra['sendcloud_data']['parcel']['country']
        if delivery.order.associate_with_delivery_items:
            delivery_items = delivery.deliveryitem_set.all()
            weight = sum([di.item.quantity * Decimal(di.item.product.get_weight()) for di in delivery_items])
            weight = max(weight, Decimal('0.001')).quantize(Decimal('0.000'))
        else:
            weight = delivery.order.extra['sendcloud_data']['parcel']['weight']
        insured_value = sum([di.item.line_total for di in delivery_items])
        cheapest_destination = ShippingDestination.objects.filter(
            shipping_method__carrier=carrier,
            country=destination_country,
            shipping_method__min_weight__lte=weight,
            shipping_method__max_weight__gte=weight,
        ).order_by('price').first()
        if not cheapest_destination:
            msg = "No shipping destination for carrier: {carrier}"
            raise ValidationError(msg.format(carrier=carrier))
        parcel = dict(
            delivery.order.extra['sendcloud_data']['parcel'],
            order_number=delivery.order.get_number(),
            request_label=True,
            weight=str(weight),
            shipment={'id': cheapest_destination.shipping_method_id},
            insured_value=math.ceil(insured_value / 100) * 100,
        )
        try:
            response = requests.post(self.create_parcel_url, json={'parcel': parcel}, auth=self.credentials)
            response_data = response.json()
            if response.status_code == 200:
                if not response_data['parcel'].get('label'):
                    raise Exception(_("Missing shipping label in response data['parcel']"))
                delivery.shipping_id = response_data['parcel']['id']
            else:
                raise Exception(response_data['error']['message'])
        except Exception as exc:
            raise ValidationError(self.error_message.format(exc))

    def withdraw_delivery(self, delivery):
        cancel_parcel_url = self.cancel_parcel_url.format(delivery.shipping_id)
        response = requests.post(cancel_parcel_url, auth=self.credentials)
        if response.status_code >= 200 and response.status_code <= 299:
            delivery.delete()


class SendcloudShippingModifiers(list):
    """
    A list of possible shipping modifiers for this provider
    """
    def __init__(self):
        try:
            ShippingMethod.objects.exists()
        except (OperationalError, ProgrammingError):
            return  # in case the database table does not exist yet
        for carrier in ShippingMethod.objects.values_list('carrier', flat=True).distinct():
            name = 'Sendcloud{}Modifier'.format(carrier.title())
            attrs = {
                'carrier': carrier,
                'identifier': 'sendcloud:{}'.format(carrier),
            }
            self.append(type(str(name), (SendcloudShippingModifierBase,), attrs))
