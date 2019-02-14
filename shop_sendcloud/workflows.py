# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from shop.modifiers.pool import cart_modifiers_pool
from shop_sendcloud.modifiers import SendcloudShippingModifierBase


class SendclouldWorkflowMixin(object):
    def withdraw_from_delivery(self):
        for delivery in self.delivery_set.filter(shipping_id__isnull=False, shipping_method__startswith='sendcloud:'):
            shipping_modifier = cart_modifiers_pool.get_active_shipping_modifier(delivery.shipping_method)
            assert isinstance(shipping_modifier, SendcloudShippingModifierBase)
            shipping_modifier.withdraw_delivery(delivery)
