from django.db import models
from django.utils.translation import ugettext_lazy as _

class SendCloudSenderAddress(models.Model):
    '''
    This model represents Sendclouds sender address
    https://docs.sendcloud.sc/api/v2/shipping/#sender-address
    When creating a parcel at Sendcloud we will need a sender_address field set
    '''

    id = models.IntegerField(
        _('Sendcloud ID'),
        primary_key=True
    )

    default_address = models.BooleanField(
        _('Default address'),
        default=False
    )

    company_name = models.CharField(
        _('Company Name'),
        max_length=255,
        default=''
    )

    contact_name = models.CharField(
        _('Contact Name'),
        max_length=255,
        default=''
    )
    
    email = models.CharField(
        _('Main E-Mail address'),
        max_length=255,
        default=''
    )

    telephone = models.CharField(
        _('Phone number'),
        max_length=255,
        default=''
    )
    
    street = models.CharField(
        _("Street"),
        max_length=255,
        default=''
    )

    house_number = models.CharField(
        _('House number'),
        max_length=100,
        default=''
    )

    postal_box = models.CharField(
        _('Postal box'),
        max_length=255,
        default=''
    )

    city = models.CharField(
        _('City'),
        max_length=255,
        default=''
    )

    postal_code = models.CharField(
        _("Postal Code"),
        max_length=15,
        default=''
    )

    country = models.CharField(
        _('Country code'),
        max_length=255,
        default=''
    )

    vat_number = models.CharField(
        _('VAT number'),
        max_length=100,
        blank=True,
        null=True,
        default=''
    )
    
    coc_number = models.CharField(
        _('COC number'),
        max_length=100,
        blank=True,
        null=True,
        default=''
    )

    eori_number = models.CharField(
        _('EORI number'),
        max_length=100,
        blank=True,
        null=True,
        default=''
    )