# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import requests

from django.conf import settings
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _
from django_fsm import transition

from shop.models.delivery import DeliveryModel
from shop.shipping.workflows import CommissionGoodsWorkflowMixin, PartialDeliveryWorkflowMixin


class SendclouldWorkflowBase(object):
    create_parcel_url = 'https://panel.sendcloud.sc/api/v2/parcels/'
    cancel_parcel_url = 'https://panel.sendcloud.sc/api/v2/parcels/{}/cancel'
    credentials = settings.SHOP_SENDCLOUD['API_KEY'], settings.SHOP_SENDCLOUD['API_SECRET']
    error_message = _("Parcel can not be delivered. Reason: {}")

    @transition(field='status', source='*', target='ship_goods')
    def ship_goods(self, by=None):
        """Invoked by SendCloudOrderAdminMixin.passthrough_shipping_label()."""
        # also prevent rendering the "Ship the goods" button

    @transition(field='status', source='request_shipping_label', target='ready_for_delivery')
    def prepare_for_delivery(self, by=None):
        """Put the parcel into the outgoing delivery."""

    def withdraw_from_delivery(self):
        for delivery in self.delivery_set.filter(shipping_id__isnull=False):
            cancel_parcel_url = self.cancel_parcel_url.format(delivery.shipping_id)
            response = requests.post(cancel_parcel_url, auth=self.credentials)
            if response.status_code >= 200 and response.status_code <= 299:
                delivery.delete()


class SingularOrderWorkflowMixin(SendclouldWorkflowBase):
    """
    Add this workflow mixin class to SHOP_ORDER_WORKFLOWS if orders always are shipped altogether.
    Otherwise use `CommonOrderWorkflowMixin` from below.
    """
    def __init__(self, *args, **kwargs):
        if not isinstance(self, CommissionGoodsWorkflowMixin):
            msg = "SingularOrderWorkflowMixin may only be used in combination with CommissionGoodsWorkflowMixin"
            raise ImproperlyConfigured(msg)
        super(SingularOrderWorkflowMixin, self).__init__(*args, **kwargs)

    def clean(self):
        """
        Create a parcel object at SendCloud. During this operation errors might be reported, therefore we do
        this in this `clean` method, so that they can be reported by the admin backend, rather than the
        `shipping_label` method.
        """
        super(SingularOrderWorkflowMixin, self).clean()
        if self._fsm_requested_transition == ('status', 'print_shipping_label'):
            if self.delivery_set.exists():
                raise ValidationError(_("Double attempt to print shipping label"))
            parcel = self.extra['sendcloud_data']['parcel']
            parcel.update(order_number=self.get_number(), request_label=True)
            try:
                response = requests.post(self.create_parcel_url, json={'parcel': parcel}, auth=self.credentials)
                response_data = response.json()
                if response.status_code == 200:
                    if not response_data['parcel'].get('label'):
                        raise Exception(_("Missing shipping label in response data['parcel']"))
                    DeliveryModel.objects.create(order=self, shipping_id=response_data['parcel']['id'])
                else:
                    raise Exception(response_data['error']['message'])
            except Exception as exc:
                raise ValidationError(self.error_message.format(exc))

    @transition(field='status', source='pack_goods', target='request_shipping_label',
                custom=dict(admin=True, button_name=_("Print Shipping Label")))
    def print_shipping_label(self, by=None):
        """
        Since creating a parcel object can fail, printing the shipping label is performed
        in method `clean()`
        """


class CommonOrderWorkflowMixin(SendclouldWorkflowBase):
    """
    Add this workflow mixin class to SHOP_ORDER_WORKFLOWS if partial delivery is enabled.
    Otherwise use `SingularOrderWorkflowMixin` from above.
    """
    def __init__(self, *args, **kwargs):
        if not isinstance(self, PartialDeliveryWorkflowMixin):
            msg = "CommonOrderWorkflowMixin may only be used in combination with PartialDeliveryWorkflowMixin"
            raise ImproperlyConfigured(msg)
        super(CommonOrderWorkflowMixin, self).__init__(*args, **kwargs)

    def ready_for_shipping(self):
        """
        Condition for state transition: True is prepared but unshipped deliveries exist.
        """
        return self.delivery_set.filter(shipped_at__isnull=True).exists()

    @transition(field='status', source='*', target='request_shipping_label',
                conditions=[ready_for_shipping],
                custom=dict(admin=True, button_name=_("Print Shipping Label")))
    def print_shipping_label(self, by=None):
        """
        Since creating a parcel object can fail, printing the shipping label is performed
        by each delivery object inside its method `clean()`
        """
