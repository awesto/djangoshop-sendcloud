# SendCloud Shipping Provider Integration for django-SHOP

This integrates the **SendCloud** API for **django-SHOP** version 1.0 and above.


## Installation

for django-SHOP version 1.0 and later:

```
pip install djangoshop-sendcloud<1.1
```


## Preparation

At [SendCloud](https://panel.sendcloud.sc/) create an account.

In your personal account settings, click on **Settings**. There:

* Add a **Sender Address**.
* In **Financial > Direct Debit** add your recurring payment settings. There your bank account is
  charged with € 0.01, but this may take a few hours or even one day until everything is checked.
* In **Selected Shop** select **SendCloud API** with a name of your choice. There, extract the
  **Public Key** and the **Secret Key** (see below).


## Configuration

In `settings.py` of the merchant's project:

Add `'shop_sendcloud'` to `INSTALLED_APPS`.

Add `'shop_sendcloud.modifiers.SendcloudShippingModifier'` to the list of `SHOP_CART_MODIFIERS`.

Add `'shop_sendcloud.shipping.OrderWorkflowMixin'` to the list of `SHOP_ORDER_WORKFLOWS`.

If you run **django-SHOP** with partial delivery, replace the `OrderItemSerializer` with the one provided:
`SHOP_ORDER_ITEM_SERIALIZER = 'shop_sendcloud.serializers.OrderItemSerializer'`
and change the workflow to:

```python
SHOP_ORDER_WORKFLOWS = [
    ...
    'shop_sendcloud.workflows.CommonOrderWorkflowMixin',
    'shop.shipping.workflows.PartialDeliveryWorkflowMixin',
]
```

Otherwise, without partial delivery, change the workflow to:

```python
SHOP_ORDER_WORKFLOWS = [
    ...
    'shop_sendcloud.workflows.SingularOrderWorkflowMixin',
    'shop.shipping.workflows.CommissionGoodsWorkflowMixin',
]
```

Add the **Public Key** and the **Secret Key** as provided by SendCloud (see above):

```python
SHOP_SENDCLOUD = {
  'API_KEY': '<public-key-as-provided-by-SendCloud>',
  'API_SECRET': '<secret-key-as-provided-by-SendCloud>',
}
```

Since SendClouds sets the Shipping ID for us, we disable that field in the
backend, using `SHOP_MANUAL_SHIPPING_ID = False`.

**SendCloud** requires a specific address model, therefore ensure that you "materialize" the one
provided with **djangoshop-sendcloud** and not the defaults from `shop/models/defaults/address`.

Typically, it's enough to import the alternative classes for `BillingAddress`, `ShippingAddress`
and `Customer` into `models.py` of your merchant implementation:

```python
from shop_sendcloud.models.address import BillingAddress, ShippingAddress
from shop_sendcloud.models.customer import Customer
```


## Initialization

Create two additional database tables as required by **djangoshop-sendcloud**:

```bash
python manange.py migrate djangoshop_sendcloud
```

Finally, load all possible shipping options into your shop:

```bash
python manange.py sendcloud_import
```
remember to run this job on a regular basis, say once a week, to update shipping prices.


## Usage

When **django-SHOP** renders the form **Shipping Method** inside the checkout view, additional
options will be available. For each carrier configured in the **SendCloud** backend, an extra radio
button appears. Whatever the customer selects, will be stored inside **django-SHOP**'s `OrderModel`.

In the Django Admin backend, only after fulfilling the order, a new button apprears named
**PRINT SHIPPING LABEL**. Clicking on that button fetches a PDF document from the SendCloud API and
forwards it to the Django Admin interface, from where it can be printed out.
