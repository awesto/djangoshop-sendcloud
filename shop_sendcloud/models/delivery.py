# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from decimal import Decimal
import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from shop.models.delivery import BaseDelivery
from shop_sendcloud.models import ShippingDestination


class Delivery(BaseDelivery):
    """Materialized Delivery Model to be used for partial deliveries with SendCloud"""
    create_parcel_url = 'https://panel.sendcloud.sc/api/v2/parcels/'
    credentials = settings.SHOP_SENDCLOUD['API_KEY'], settings.SHOP_SENDCLOUD['API_SECRET']
    error_message = _("Parcel can not be delivered. Reason: {}")

    def clean(self):
        """
        For each prepared delivery, create a parcel object at SendCloud. Weight and insurance are recomputed.
        During this state transition, errors might occur, therefore we do it inside a `clean` method, so that
        potential errors can be reported by the admin backend.
        """
        if self.order._fsm_requested_transition == ('status', 'print_shipping_label'):
            if self.shipping_id or not self.order.extra['shipping_modifier'].startswith('sendcloud:'):
                return
            carrier = self.order.extra['shipping_modifier'][len('sendcloud:'):]
            parcel = self.order.extra['sendcloud_data']['parcel']
            parcel.update(order_number=self.order.get_number(), request_label=True)
            delivery_items = self.deliveryitem_set.all()
            try:
                # since our order is splitted into many deliveries, recompute weight and insurance
                weight = sum([di.item.quantity * Decimal(di.item.product.get_weight()) for di in delivery_items])
                insured_value = sum([di.item.line_total for di in delivery_items])
                cheapest_destination = ShippingDestination.objects.filter(
                    shipping_method__carrier=carrier,
                    country=parcel['country'],
                    shipping_method__min_weight__lte=weight,
                    shipping_method__max_weight__gte=weight,
                ).order_by('price').first()
                parcel.update(
                    weight=str(weight.quantize(Decimal('0.000'))),
                    shipment={'id': cheapest_destination.shipping_method_id},
                    insured_value=int(insured_value),
                )
                response = requests.post(self.create_parcel_url, json={'parcel': parcel}, auth=self.credentials)
                response_data = response.json()
                if response.status_code >= 200 and response.status_code <= 299:
                    self.shipping_id = response_data['parcel']['id']
                else:
                    raise Exception(response_data['error']['message'])
            except Exception as exc:
                raise ValidationError(self.error_message.format(exc))
