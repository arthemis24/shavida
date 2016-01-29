# -*- coding: utf-8 -*-
from django.conf import settings

from django.db import models
from django.utils.translation import gettext as _

from Shavida.utils import is_content_vendor

DEFAULT_SITE_IMAGE = 'cms/default_site_img.jpg'


class FlatPage(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField()
    content = models.TextField()
    show_banner = models.BooleanField(default=False)
    banner = models.FileField(default=DEFAULT_SITE_IMAGE, upload_to='cms/banners')
    show_in_footer = models.BooleanField(default=False,
                                         help_text=_("Check to make the link appear in the site footer."))

    def __unicode__(self):
        return self.title


class SiteConfig(models.Model):
    name = models.CharField(max_length=30,
                            help_text=_("Name of the configuration."))
    slogan = models.CharField(max_length=60,
                              help_text=_("Slogan of your website."))
    summary = models.CharField(max_length=255,
                               help_text=_("Short summary describing your business. 255 characters max."))
    email = models.EmailField(help_text=_("The main e-mail for your customers to contact you."))
    phone_1 = models.CharField(max_length=18, blank=True,
                               help_text=_("Main phone number for your customers to contact you."))
    phone_2 = models.CharField(max_length=18, blank=True,
                               help_text=_("Secondary phone number for your customers to contact you."))
    facebook_link = models.URLField(blank=True,
                                    help_text=_("Facebook link. Eg: https://www.facebook.com/myvodstore"))
    twitter_link = models.URLField(blank=True,
                                   help_text=_("Twitter link. Eg: https://www.twitter.com/myvodstore"))
    google_plus_link = models.URLField(blank=True,
                                       help_text=_("Google+ link. Eg: https://www.googleplus.com/myvodstore"))
    is_active = models.BooleanField(default=False,
                                    help_text=_("Check/Uncheck to activate/deactivate this configuration."))
    vod = models.BooleanField(default=False, editable=is_content_vendor,
                              help_text=_("Check/Uncheck to activate/deactivate VoD."))
    vod_data_source = models.TextField(blank=True,
                                       help_text=_("List of sources to check to retrieve video files. "
                                                   "Separate by commas. (Eg: http://myserver.net/vod1, rtmp://src.net/vod2)"))
    google_analytics = models.TextField(blank=True,
                                       help_text=_("Google Analytics tracking code."))

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = _('Configurations of the platform')

    # def save(self, *args, **kwargs):
    #     # Ensures that always one and only one SiteConfig remains with is_active=True
    #     if self.is_active:
    #         for config in SiteConfig.objects.filter(is_active=True):
    #             config.is_active = False
    #             super(SiteConfig, config).save(*args, **kwargs)
    #     else:
    #         if SiteConfig.objects.filter(is_active=True).count() == 1:
    #             self.is_active = True
    #     super(SiteConfig, self).save(*args, **kwargs)
