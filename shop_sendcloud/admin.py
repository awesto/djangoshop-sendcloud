# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import requests
from django.conf import settings
from django.conf.urls import url
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.utils.six.moves.urllib.parse import urlparse
from shop.models.delivery import DeliveryModel


class SendCloudOrderAdminMixin(object):
    change_form_template = 'shop_sendcloud/order_change_form.html'
    parcel_label_url = 'https://panel.sendcloud.sc/api/v2/labels/{}'
    credentials = settings.SHOP_SENDCLOUD['API_KEY'], settings.SHOP_SENDCLOUD['API_SECRET']

    class Media:
        js = ['shop/admin/js/order_change_form.js']
        css = {
            'all': ['shop/admin/css/order_change_form.css']
        }

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        assert obj is not None
        if obj.status == 'ready_for_delivery':
            context.setdefault('parcel_label_urls', [])
            try:
                for delivery in obj.delivery_set.filter(shipping_id__isnull=False, shipped_at__isnull=True):
                    url = self.parcel_label_url.format(delivery.shipping_id)
                    response = requests.get(url, auth=self.credentials)
                    if response.status_code == 200:
                        parcel = response.json()
                        context['parcel_label_urls'].append(parcel['label']['normal_printer'][2])  # TODO: make this configurable
            except:
                messages.add_message(request, messages.INFO, "No SendCloud label could be printed.")
        return super(SendCloudOrderAdminMixin, self).render_change_form(request, context, add, change, form_url, obj)

    def get_urls(self):
        my_urls = [
            url(r'^print_shipping_label/$', self.admin_site.admin_view(self.passthrough_shipping_label),
                name='print_shipping_label'),
        ]
        my_urls.extend(super(SendCloudOrderAdminMixin, self).get_urls())
        return my_urls

    def passthrough_shipping_label(self, request):
        label_url = request.GET.get('url')
        res = requests.get(label_url, auth=self.credentials)
        if res.status_code == 200:
            # mark the parcel label as printed
            try:
                parcel_id = urlparse(label_url).path.split('/')[-1]
                delivery = DeliveryModel.objects.get(shipping_id=parcel_id)
            except DeliveryModel.DoesNotExist:
                parcel_id = None
            else:
                delivery.shipped_at = timezone.now()
                delivery.save(update_fields=['shipped_at'])
        else:
            parcel_id = None
        response = HttpResponse(res.content, status=res.status_code, content_type=res.headers['content-type'])
        if parcel_id:
            response['Content-Disposition'] = 'filename="parcel_label_{}.pdf"'.format(parcel_id)
        return response
