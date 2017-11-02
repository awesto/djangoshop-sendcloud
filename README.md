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
    'PURCHASE_DESCRIPTION': _("Thanks for purchasing at MyShop"),
}
```

Add ``'shop_sendcloud.modifiers.SendcloudShippingModifier'`` to the list of ``SHOP_CART_MODIFIERS``.

Add ``'shop_sendcloud.shipping.OrderWorkflowMixin'`` to the list of ``SHOP_ORDER_WORKFLOWS``.


## Changes

### 0.12
* Initial working release.
