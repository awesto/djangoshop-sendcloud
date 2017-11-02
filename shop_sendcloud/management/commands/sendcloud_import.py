# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import requests

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext_lazy as _

from shop.money import MoneyMaker
from shop_sendcloud.models import ShippingMethod, ShippingDestination

EUR = MoneyMaker('EUR')


class Command(BaseCommand):
    help = _("Fetch shipping method fees from SendCloud.")
    download_url = 'https://panel.sendcloud.sc/api/v2/shipping_methods'
    credentials = settings.SHOP_SENDCLOUD['API_KEY'], settings.SHOP_SENDCLOUD['API_SECRET']

    def handle(self, verbosity, *args, **options):
        response = requests.get(self.download_url, auth=self.credentials, stream=True)
        for sm in response.json()['shipping_methods']:
            id = sm.pop('id')
            default_price = sm.pop('price')
            sm.pop('service_point_input', None)
            countries = sm.pop('countries', [])
            try:
                shipping_method, created = ShippingMethod.objects.get_or_create(id=id, defaults=sm)
            except Exception as ex:
                raise CommandError("In id={}: {}".format(id, ex))
            for dst in countries:
                dst['country'] = dst.pop('iso_2')
                iso_3 = dst.pop('iso_3')
                dst.pop('name', None)
                dst.setdefault('price', default_price)
                try:
                    ShippingDestination.objects.get_or_create(shipping_method=shipping_method, defaults=dst)
                except Exception as ex:
                    raise CommandError("In shipping_id={} country={}: {}".format(shipping_method.id, iso_3, ex))
