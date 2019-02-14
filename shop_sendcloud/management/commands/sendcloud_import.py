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
    INCLUDE_CARRIERES = settings.SHOP_SENDCLOUD.get('INCLUDE_CARRIERES')
    EXCLUDE_CARRIERES = settings.SHOP_SENDCLOUD.get('EXCLUDE_CARRIERES', ['sendcloud'])

    def handle(self, verbosity, *args, **options):
        response = requests.get(self.download_url, auth=self.credentials)
        if response.status_code != 200:
            msg = "Failed to import carriers from SendCloud. Reason: {message}"
            raise CommandError(msg.format(**response.json()['error']))
        response_data = response.json()
        for sm in response_data['shipping_methods']:
            if isinstance(self.INCLUDE_CARRIERES, (list, tuple)):
                if sm['carrier'] not in self.INCLUDE_CARRIERES:
                    continue
            elif isinstance(self.EXCLUDE_CARRIERES, (list, tuple)):
                if sm['carrier'] in self.EXCLUDE_CARRIERES:
                    continue

            id = sm.pop('id')
            default_price = sm.pop('price')
            sm.pop('service_point_input', None)
            countries = sm.pop('countries', [])
            try:
                shipping_method, created = ShippingMethod.objects.update_or_create(id=id, defaults=sm)
                if created:
                    destination_ids = []
                else:
                    destination_ids = list(shipping_method.destinations.values_list('id', flat=True))
            except Exception as ex:
                raise CommandError("In id={}: {}".format(id, ex))
            for dst in countries:
                country = dst.pop('iso_2')
                iso_3 = dst.pop('iso_3')
                dst.pop('id', None)
                dst.pop('name', None)
                dst.setdefault('price', default_price)
                try:
                    destination, created = ShippingDestination.objects.update_or_create(
                        shipping_method=shipping_method, country=country, defaults=dst)
                    if not created and destination.id in destination_ids:
                        destination_ids.remove(destination.id)
                except Exception as ex:
                    raise CommandError("In shipping_id={} country={}: {}".format(shipping_method.id, iso_3, ex))
            # remove destinations which haven't been updated
            shipping_method.destinations.filter(id__in=destination_ids).delete()
