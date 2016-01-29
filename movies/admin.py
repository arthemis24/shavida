# -*- coding: utf-8 -*-
import re
from django.conf import settings
from django.contrib import admin
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import slugify
import random

from ikwen.models import Member
from import_export import resources
from import_export.admin import ImportExportMixin
from movies.models import Movie, Category, Series, SeriesEpisode, Trailer
from sales.models import ContentUpdate


def add_movies_to_top20(modeladmin, request, queryset):
    top_category = Category.objects.get(slug='top')
    for movie in queryset:
        movie_categories = list(movie.categories.all())
        if top_category in movie_categories:
            return False
        else:
            movie.categories.add(top_category)


def remove_movies_from_top20(modeladmin, request, queryset):
    top_category = Category.objects.get(slug='top')
    for movie in queryset:
        movie_categories = list(movie.categories.all())
        if top_category not in movie_categories:
            return
        movie.categories.remove(top_category)


def add_media_to_delete_list(modeladmin, request, queryset):
    member = request.user
    try:
        update = ContentUpdate.objects.get(member=member, status=ContentUpdate.PENDING)
    except ContentUpdate.DoesNotExist:
        update = ContentUpdate(member=member)
    delete_list = []
    delete_list_size = 0
    update.movies_delete_list.clear()
    update.series_episodes_delete_list.clear()
    for media in queryset:
        if type(media).__name__ == 'Movie':
            update.movies_delete_list.add(media)
        else:
            update.series_episodes_delete_list.add(media)
        delete_list_size += media.size
        for filename in media.filename.split(','):
            delete_list.append(filename.strip())
    update.delete_list = ','.join(delete_list)
    update.delete_list_size = delete_list_size
    update.save()


add_movies_to_top20.short_description = "Add selected movies in Top 20"
remove_movies_from_top20.short_description = "Remove selected movies from Top 20"
add_media_to_delete_list.short_description = "Mark for deletion"


def remove_special_words(s):
    s = re.sub("^the ", '', s)
    s = re.sub("^at ", '', s)
    s = re.sub("^in ", '', s)
    s = re.sub("^le ", '', s)
    s = re.sub("^la ", '', s)
    s = re.sub("^les ", '', s)
    s = re.sub("^l'", '', s)
    s = re.sub("^un ", '', s)
    s = re.sub("^une ", '', s)
    s = re.sub("^des ", '', s)
    s = re.sub("^d'", '', s)
    s = re.sub("^de ", '', s)
    s = re.sub("^du ", '', s)
    s = re.sub("^a ", '', s)
    s = re.sub("^et ", '', s)
    s = re.sub("^en ", '', s)
    s = s.replace(" the ", " ")\
        .replace(" at ", " ")\
        .replace(" in ", " ")\
        .replace(" of ", " ")\
        .replace(" le ", " ")\
        .replace(" la ", " ")\
        .replace(" les ", " ")\
        .replace(" l'", " ")\
        .replace(" un ", " ")\
        .replace(" une ", " ")\
        .replace(" des ", " ")\
        .replace(" d'", " ")\
        .replace(" de ", " ")\
        .replace(" du ", " ")\
        .replace(" a ", " ")\
        .replace(" et ", " ")\
        .replace(" en ", " ")\
        .replace(" 1", "")\
        .replace(" 2", "")\
        .replace(" 3", "")\
        .replace(" 4", "")\
        .replace(" 5", "")\
        .replace(" 6", "")\
        .replace(" 7", "")\
        .replace(" 8", "")\
        .replace(" 9", "")
    return s


def get_title_from_filename(filename):
    PREFIXES = ['cine_', 'da_', 'clip_', 'tuto_', 'Hd_', 'comedie_', 'oms_', 'gag_', 'xxl_', 'doc_', 'Xcamer_']
    # Strip extension
    title = filename
    idx = title.rfind('.')
    title = title[:idx]

    # Strip custom prefix
    for prefix in PREFIXES:
        title = title.replace(prefix, '')
    title = title.replace('.', ' ').replace('_', ' ')
    return title


class MovieResource(resources.ModelResource):

    def before_save_instance(self, instance, dry_run):
        title = get_title_from_filename(instance.filename)
        instance.filename = instance.filename.replace(' ', '.')
        slug = slugify(title)
        instance.slug = slug
        fake_bonus = int(random.random() * 1000) * 2
        instance.fake_orders += fake_bonus
        instance.fake_clicks = instance.fake_orders + fake_bonus
        if instance.trailer_slug:
            instance.trailer = get_object_or_404(Trailer, slug=instance.trailer_slug)
        instance.visible = False
        instance.tags = remove_special_words(title.lower()) + " " + instance.tags.lower()
        instance.title = 'IMP ' + title.capitalize()
        provider_id = getattr(settings, 'PROVIDER_ID')
        instance.provider = Member.objects.get(pk=provider_id)

    def skip_row(self, instance, original):
        if '/' in instance.filename:
            return True
        title = get_title_from_filename(instance.filename)
        slug = slugify(title)
        try:
            Movie.objects.get(filename=instance.filename)
            return True
        except Movie.DoesNotExist:
            try:
                Movie.objects.get(slug=slug)
                return True
            except Movie.DoesNotExist:
                return False

    class Meta:
        model = Movie
        skip_unchanged = True
        exclude = ('poster', 'synopsis', 'visible', 'categories')
        import_id_fields = ('filename', 'fake_orders', 'price', 'size', 'groups', 'tags')


class SeriesResource(resources.ModelResource):

    def before_save_instance(self, instance, dry_run):
        slug = slugify(instance.title)
        instance.slug = slug
        if instance.trailer_slug:
            instance.trailer = get_object_or_404(Trailer, slug=instance.trailer_slug)
        instance.visible = False
        instance.tags = remove_special_words(instance.title.lower()) + " " + instance.tags.lower()
        instance.title = 'IMP ' + instance.title.capitalize()
        provider_id = getattr(settings, 'PROVIDER_ID')
        instance.provider = Member.objects.get(pk=provider_id)

    def skip_row(self, instance, original):
        title = get_title_from_filename(instance.filename)
        slug = slugify(title)
        try:
            Series.objects.get(slug=slug)
            return True
        except Series.DoesNotExist:
            return False

    class Meta:
        model = Series
        skip_unchanged = True
        exclude = ('poster', 'synopsis', 'visible', 'categories')
        import_id_fields = ('title', 'season', 'price', 'episodes_count', 'groups', 'tags')


class SeriesEpisodeResource(resources.ModelResource):

    def before_save_instance(self, instance, dry_run):
        filename = instance.filename
        idx = filename.rfind('/')
        naked_filename = filename[idx + 1:]
        idx = naked_filename.rfind('.')
        title = naked_filename[:idx]
        instance.title = title
        instance.slug = slugify(title)
        fake_bonus = int(random.random() * 300)
        fake_bonus = min(fake_bonus, 200)
        instance.fake_orders += fake_bonus
        instance.fake_clicks = instance.fake_orders + fake_bonus
        provider_id = getattr(settings, 'PROVIDER_ID')
        instance.provider = Member.objects.get(pk=provider_id)

    def skip_row(self, instance, original):
        if '/' not in instance.filename:
            return True
        return False

    class Meta:
        model = SeriesEpisode
        skip_unchanged = True
        import_id_fields = ('series', 'filename', 'fake_orders', 'price', 'size')


class TrailerResource(resources.ModelResource):

    def before_save_instance(self, instance, dry_run):
        instance.title = get_title_from_filename(instance.filename)
        instance.filename = instance.filename.replace(' ', '.')
        instance.slug = slugify(instance.title)

    def skip_row(self, instance, original):
        try:
            Trailer.objects.get(filename=instance.filename)
            return True
        except Trailer.DoesNotExist:
            return False

    class Meta:
        model = Trailer
        skip_unchanged = True
        import_id_fields = ('filename', 'size', 'duration')


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'previews_title', 'smart', 'previews_length', 'order_of_appearance', 'appear_in_main')
    list_filter = ('smart', 'appear_in_main', 'visible')
    prepopulated_fields = {"slug": ("title",)}

    def save_model(self, request, obj, form, change):
        obj.title = obj.title.strip()
        obj.slug = obj.slug.strip()
        obj.previews_title = obj.previews_title.strip()
        super(CategoryAdmin, self).save_model(request, obj, form, change)


class MovieAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_class = MovieResource
    list_display = ('title', 'size', 'duration', 'price', 'orders', 'clicks', 'filename', 'visible')
    list_filter = ('created_on', 'price', 'visible')
    fieldsets = (
        (None, {'fields': ('title', 'slug', 'release', 'synopsis', 'size', 'duration', 'filename', 'trailer_slug')}),
        ('Meta', {'fields': ('visible', 'is_adult', 'groups', 'tags', )}),
        ('Interest', {'fields': ('clicks', 'fake_clicks', 'orders', 'fake_orders', )}),
        ('Important dates', {'fields': ('created_on', 'updated_on',)}),
    )
    ordering = ('-id', '-title', '-release', '-clicks', '-orders')
    search_fields = ('title', 'filename', )
    readonly_fields = ('provider', 'orders', 'clicks', 'created_on', 'updated_on')
    date_hierarchy = 'created_on'
    save_on_top = True
    prepopulated_fields = {"slug": ("title",), "tags": ("title",), "groups": ("title",)}
    actions = [add_movies_to_top20, remove_movies_from_top20]

    def save_model(self, request, obj, form, change):
        obj.title = obj.title.strip()
        obj.slug = obj.slug.strip()
        if obj.trailer_slug:
            obj.trailer_slug = obj.trailer_slug.split()
        obj.filename = obj.filename.strip()
        provider_id = getattr(settings, 'PROVIDER_ID')
        obj.provider = Member.objects.get(pk=provider_id)
        for category in obj.categories:
            if category.is_adult:
                obj.is_adult = True
                break
        super(MovieAdmin, self).save_model(request, obj, form, change)


class SeriesAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_class = SeriesResource
    list_display = ('title', 'season', 'episodes_count', 'price', 'visible')
    list_filter = ('created_on', 'visible')
    fieldsets = (
        (None, {'fields': ('title', 'season', 'slug', 'episodes_count', 'release', 'synopsis', 'trailer_slug', )}),
        ('Meta', {'fields': ('visible', 'is_adult', 'groups', 'tags', )}),
        ('Important dates', {'fields': ('created_on', 'updated_on',)}),
    )
    readonly_fields = ('provider', 'created_on', 'updated_on')
    ordering = ('-id', '-title', '-release')
    search_fields = ('title', )
    date_hierarchy = 'created_on'
    save_on_top = True
    prepopulated_fields = {"slug": ("title",), "tags": ("title",), "groups": ("title",)}
    actions = [add_movies_to_top20, remove_movies_from_top20]

    def save_model(self, request, obj, form, change):
        obj.title = obj.title.strip()
        obj.slug = obj.slug.strip()
        if obj.trailer_slug:
            obj.trailer_slug = obj.trailer_slug.split()
        provider_id = getattr(settings, 'PROVIDER_ID')
        obj.provider = Member.objects.get(pk=provider_id)
        for category in obj.categories:
            if category.is_adult:
                obj.is_adult = True
                break
        for episode in obj.seriesepisode_set.all():
            episode.is_adult = obj.is_adult
            episode.release = obj.release
            episode.save()
        super(SeriesAdmin, self).save_model(request, obj, form, change)


class SeriesEpisodeAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_class = SeriesEpisodeResource
    list_display = ('series', 'title', 'orders', 'clicks', 'filename')
    list_filter = ('series', 'created_on')
    fieldsets = (
        (None, {'fields': ('title', 'slug', 'size', 'duration', 'filename')}),
        ('Meta', {'fields': ('is_adult', 'groups', 'tags', )}),
        ('Interest', {'fields': ('clicks', 'fake_clicks', 'orders', 'fake_orders', )}),
        ('Important dates', {'fields': ('created_on', 'updated_on',)}),
    )
    ordering = ('-id', '-title')
    readonly_fields = ('provider', 'orders', 'clicks', 'size', 'created_on', 'updated_on')
    search_fields = ('title', 'filename', )
    date_hierarchy = 'created_on'
    save_on_top = True
    prepopulated_fields = {"slug": ("title",)}

    def save_model(self, request, obj, form, change):
        obj.title = obj.title.strip()
        obj.slug = obj.slug.strip()
        obj.filename = obj.filename.strip()
        obj.is_adult = obj.series.is_adult
        obj.release = obj.series.release
        provider_id = getattr(settings, 'PROVIDER_ID')
        obj.provider = Member.objects.get(pk=provider_id)
        super(SeriesEpisodeAdmin, self).save_model(request, obj, form, change)


class TrailerAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_class = TrailerResource
    list_display = ('title', 'slug', 'filename', 'size', 'duration', )
    readonly_fields = ('clicks',)
    ordering = ('-id', '-title')


admin.site.register(Movie, MovieAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Series, SeriesAdmin)
admin.site.register(SeriesEpisode, SeriesEpisodeAdmin)
admin.site.register(Trailer, TrailerAdmin)



