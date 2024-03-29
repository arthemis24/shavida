# -*- coding: utf-8 -*-

__author__ = 'Roddy MBOGNING'

from django.db.models.fields.files import ImageField, ImageFieldFile
from PIL import Image
import os


def _add_suffix(suffix, s):
    """
    Modifies a string (filename, URL) containing an image filename, to insert
    '.suffix' (Eg: .small, .thumb, etc.) before the file extension (which is changed to be '.jpg').
    """
    parts = s.split(".")
    parts.insert(-1, suffix)
    if parts[-1].lower() not in ['jpeg', 'jpg']:
        parts[-1] = 'jpg'
    return ".".join(parts)


class MultiImageFieldFile(ImageFieldFile):

    def _get_lowqual_path(self):
        return _add_suffix('lowqual', self.path)
    lowqual_path = property(_get_lowqual_path)

    def _get_lowqual_url(self):
        return _add_suffix('lowqual', self.url)
    lowqual_url = property(_get_lowqual_url)

    def _get_small_path(self):
        return _add_suffix('small', self.path)
    small_path = property(_get_small_path)

    def _get_small_url(self):
        return _add_suffix('small', self.url)
    small_url = property(_get_small_url)

    def _get_thumb_path(self):
        return _add_suffix('thumb', self.path)
    thumb_path = property(_get_thumb_path)

    def _get_thumb_url(self):
        return _add_suffix('thumb', self.url)
    thumb_url = property(_get_thumb_url)

    def save(self, name, content, save=True):
        super(MultiImageFieldFile, self).save(name, content, save)
        img = Image.open(self.path)
        #Save the low quality version of the image with the original dimensions
        if self.field.lowqual > 0: #Create the Low Quality version only if lowqual is set
            IMAGE_WIDTH_LIMIT = 800 #Too big images are of no use on this web site
            lowqual_size = img.size if img.size[0] <= IMAGE_WIDTH_LIMIT else IMAGE_WIDTH_LIMIT, IMAGE_WIDTH_LIMIT
            img.thumbnail(lowqual_size, Image.NEAREST)
            img.save(self.lowqual_path, 'JPEG', quality=self.field.lowqual)
        #Save the .small version of the image
        img = Image.open(self.path)
        img.thumbnail(
            (self.field.small_side, self.field.small_side),
            Image.ANTIALIAS
        )
        img.save(self.small_path, 'JPEG', quality=90)
        #Save the .thumb version of the image
        img = Image.open(self.path)
        img.thumbnail(
            (self.field.thumb_side, self.field.thumb_side),
            Image.ANTIALIAS
        )
        img.save(self.thumb_path, 'JPEG', quality=78)

    def delete(self, save=True):
        if os.path.exists(self.lowqual_path):
            os.remove(self.lowqual_path)
        if os.path.exists(self.small_path):
            os.remove(self.small_path)
        if os.path.exists(self.thumb_path):
            os.remove(self.thumb_path)
        super(MultiImageFieldFile, self).delete(save)


class MultiImageField(ImageField):
    """
    Behaves like a regular ImageField, but stores extra (JPEG) images providing get_FIELD_lowqual_url(), get_FIELD_small_url(), 
    get_FIELD_thumb_url(), get_FIELD_small_filename(), get_FIELD_lowqual_filename() and get_FIELD_thumb_filename().
    Accepts three additional, optional arguments: lowqual, small_side and thumb_side,
    respectively defaulting to 15(%), 250 and 60 (pixels).
    """
    attr_class = MultiImageFieldFile

    def __init__(self, lowqual=0, small_side=300, thumb_side=60, *args, **kwargs):
        self.lowqual = lowqual
        self.small_side = small_side
        self.thumb_side = thumb_side
        super(MultiImageField, self).__init__(*args, **kwargs)
