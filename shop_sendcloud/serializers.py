# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.core.cache import cache
from django.core import exceptions
from django.utils.translation import ugettext_lazy, ugettext_noop

import requests
from rest_framework import serializers
from shop.conf import app_settings
from shop.models.delivery import DeliveryItemModel
from shop.serializers.bases import BaseOrderItemSerializer


# status messages supplied by SendCloud via https://<apikey>:<apisecret>@panel.sendcloud.sc/api/v2/parcels/statuses
ugettext_noop("Announced")  # 1
ugettext_noop("Announced: not collected")  # 13
ugettext_noop("Announcement failed")  # 1002
ugettext_noop("message': 'En route to sorting center")  # 3
ugettext_noop("Delivery delayed")  # 4
ugettext_noop("Sorted")  # 5
ugettext_noop("Not sorted")  # 6
ugettext_noop("Being sorted")  # 7
ugettext_noop("Delivery attempt failed")  # 8
ugettext_noop("Delivered")  # 11
ugettext_noop("Awaiting customer pickup")  # 12
ugettext_noop("Error collecting")  # 15
ugettext_noop("Picked up from postoffice")  # 22
ugettext_noop("Unable to deliver")  # 80
ugettext_noop("Parcel en route")  # 91
ugettext_noop("Driver en route")  # 92
ugettext_noop("Picked up at service point")  # 93
ugettext_noop("No label")  # 999
ugettext_noop("Ready to send")  # 1000
ugettext_noop("Being announced")  # 1001
ugettext_noop("Cancelled")  # 2000
ugettext_noop("Submitting cancellation request")  # 2001
ugettext_noop("Cancellation requested")  # 1999
ugettext_noop("Unknown status - check carrier track & trace page for more insights")  # 1337


class OrderItemListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        try:
            queryset = data.order_by('deliveryitem__delivery')
        except exceptions.FieldError:
            queryset = data.all()
        return super(OrderItemListSerializer, self).to_representation(queryset)


class OrderItemSerializer(BaseOrderItemSerializer):
    parcel_url = 'https://panel.sendcloud.sc/api/v2/parcels/{parcel_id}'
    credentials = settings.SHOP_SENDCLOUD['API_KEY'], settings.SHOP_SENDCLOUD['API_SECRET']

    summary = serializers.SerializerMethodField(
        help_text="Sub-serializer for fields to be shown in the product's summary.")

    delivery_status = serializers.SerializerMethodField()
    parcel = serializers.SerializerMethodField()

    class Meta(BaseOrderItemSerializer.Meta):
        fields = ['line_total', 'unit_price', 'product_code', 'quantity', 'summary',
                  'delivery_status', 'parcel', 'extra']
        list_serializer_class = OrderItemListSerializer

    def get_summary(self, order_item):
        label = self.context.get('render_label', 'order')
        serializer_class = app_settings.PRODUCT_SUMMARY_SERIALIZER
        serializer = serializer_class(order_item.product, context=self.context,
                                      read_only=True, label=label)
        return serializer.data

    def get_delivery_status(self, order_item):
        parcel = self.get_parcel(order_item)
        if parcel:
            return ugettext_lazy(parcel['status']['message'])
        return ugettext_lazy("Purchase order issued")

    def get_parcel(self, order_item):
        try:
            delivery = order_item.deliveryitem_set.get().delivery
        except DeliveryItemModel.DoesNotExist:
            return
        parcel_url = self.parcel_url.format(parcel_id=delivery.shipping_id)
        parcel = cache.get(parcel_url)
        if parcel is None:
            response = requests.get(parcel_url, auth=self.credentials)
            if response.status_code >= 200 and response.status_code <= 299:
                parcel = response.json()['parcel']
                cache.set(parcel_url, parcel, 3600)  # TODO: make this configurable
        return parcel
