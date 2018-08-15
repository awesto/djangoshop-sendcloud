# Sendcloud Shipping Provider Integration for django-shop

This integrates the Stripe for django-shop version 0.9 and above.


## Installation

for django-shop version 0.12:

```
pip install djangoshop-sendcloud
```


## Configuration

In ``settings.py`` of the merchant's project:

Add ``'shop_sendcloud'`` to ``INSTALLED_APPS``.

At [SendCloud](https://panel.sendcloud.sc/) create an account and apply for a public/private
key-pair. Then add these keys:

```
SHOP_SENDCLOUD = {
    'API_KEY': '<public-key-as-delivered-by-SendCloud>',
    'API_SECRET': '<secret-key-as-delivered-by-SendCloud>',
}
```

Add ``'shop_sendcloud.modifiers.SendcloudShippingModifier'`` to the list of ``SHOP_CART_MODIFIERS``.

Add ``'shop_sendcloud.shipping.OrderWorkflowMixin'`` to the list of ``SHOP_ORDER_WORKFLOWS``.

If you run **django-SHOP** with partial delivery, add:

``SHOP_ORDER_ITEM_SERIALIZER = 'shop_sendcloud.serializers.OrderItemSerializer'``

and append to

```
SHOP_ORDER_WORKFLOWS = [
    ...
    'shop_sendcloud.workflows.CommonOrderWorkflowMixin',
    'shop.shipping.workflows.PartialDeliveryWorkflowMixin',
]
```

otherwise, without partial delivery, append to:

```
SHOP_ORDER_WORKFLOWS = [
    ...
    'shop_sendcloud.workflows.SingularOrderWorkflowMixin',
    'shop.shipping.workflows.CommissionGoodsWorkflowMixin',
]
```


Since SendClouds set the Shipping ID for us, we disable that field in the
backend, using ``SHOP_MANUAL_SHIPPING_ID = False``.


## Changes

### 0.12
* Initial working release.
