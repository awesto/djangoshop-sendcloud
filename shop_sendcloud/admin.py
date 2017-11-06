# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import requests

from django.conf import settings
from django.conf.urls import url
from django.http import HttpResponse


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
        if obj and obj.status == 'request_shipping_label':
            for delivery in obj.delivery_set.filter(shipping_id__isnull=False, shipped_at__isnull=True):
                self.populate_context(delivery.shipping_id, context)
        return super(SendCloudOrderAdminMixin, self).render_change_form(request, context, add, change, form_url, obj)

    def populate_context(self, parcel_id, context):
        context.setdefault('parcel_label_urls', [])
        url = self.parcel_label_url.format(parcel_id)
        response = requests.get(url, auth=self.credentials)
        if response.status_code == 200:
            parcel = response.json()
            context['parcel_label_urls'].append(parcel['label']['normal_printer'][2])

    def get_urls(self):
        my_urls = [
            url(r'^print_shipping_label/$', self.admin_site.admin_view(self.passthrough_shipping_label),
                name='print_shipping_label'),
        ] + super(SendCloudOrderAdminMixin, self).get_urls()
        return my_urls

    def passthrough_shipping_label(self, request):
        label_url = request.GET.get('url')
        res = requests.get(label_url, auth=self.credentials)
        return HttpResponse(res.content, status=res.status_code, content_type=res.headers['content-type'])
