# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import requests

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django_fsm import transition

from shop.models.delivery import DeliveryModel


class OrderWorkflowMixin(object):
    TRANSITION_TARGETS = {
        'request_shipping_label': _("Shipping label requested"),
    }
    create_parcel_url = 'https://panel.sendcloud.sc/api/v2/parcels/'
    cancel_parcel_url = 'https://panel.sendcloud.sc/api/v2/parcels/{}/cancel'
    parcel_label_url = 'https://panel.sendcloud.sc/api/v2/labels/{}'
    credentials = settings.SHOP_SENDCLOUD['API_KEY'], settings.SHOP_SENDCLOUD['API_SECRET']
    error_message = _("Parcel can not be delivered. Reason: {}")

    def clean(self):
        """
        Create a parcel object at SendCloud. During this operation errors might be reported, therefore we do
        this in this `clean` method, so that they can be reported by the admin backend, rather than the
        `shipping_label` method.
        """
        super(OrderWorkflowMixin, self).clean()
        if self._fsm_requested_transition == ('status', 'print_shipping_label'):
            parcel = self.extra['sendcloud_data']['parcel']
            parcel.update(order_number=self.get_number(), request_label=True)
            try:
                response = requests.post(self.create_parcel_url, json={'parcel': parcel}, auth=self.credentials)
                response_data = response.json()
                if response.status_code >= 200 and response.status_code <= 299:
                    try:
                        delivery = DeliveryModel.objects.get(order=self)
                    except DeliveryModel.DoesNotExist:
                        DeliveryModel.objects.create(order=self, shipping_id=response_data['parcel']['id'])
                    else:
                        delivery.shipping_id=response_data['parcel']['id']
                        delivery.save()
                else:
                    raise Exception(response_data['error']['message'])
            except Exception as exc:
                raise ValidationError(self.error_message.format(exc))

    @transition(field='status', source=['ready_for_delivery'], target='request_shipping_label',
                custom=dict(admin=True, button_name=_("Print Shipping Label")))
    def print_shipping_label(self, by=None):
        """
        Print the shipping label
        """
        # for delivery in self.delivery_set.filter(shipping_id__isnull=False, shipped_at=None):
        #     parcel = {'id': delivery.shipping_id, 'request_label': True}
        #     response = requests.put(self.create_parcel_url, json={'parcel': parcel}, auth=self.credentials)
        #     assert response.status_code >= 200 and response.status_code <= 299

    def withdraw_from_delivery(self):
        for delivery in self.delivery_set.filter(shipping_id__isnull=False):
            cancel_parcel_url = self.cancel_parcel_url.format(delivery.shipping_id)
            response = requests.post(cancel_parcel_url, auth=self.credentials)
            if response.status_code >= 200 and response.status_code <= 299:
                delivery.delete()
