import itertools
import uuid

from textile import textile_restricted

from django.db import models
from django.dispatch import receiver
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from talks.events.models import Event, EventGroup


DEFAULT_COLLECTION_NAME = "My Collection"
COLLECTION_ROLES_OWNER = 'owner'
COLLECTION_ROLES_EDITOR = 'editor'
COLLECTION_ROLES_READER = 'reader'
COLLECTION_ROLES = (
    (COLLECTION_ROLES_OWNER, 'Owner'),
    (COLLECTION_ROLES_EDITOR, 'Collaborator'),
    (COLLECTION_ROLES_READER, 'Viewer'),
)


class CollectedDepartment(models.Model):
    department = models.TextField(default='')

class Collection(models.Model):

    slug = models.SlugField()
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    editor_set = models.ManyToManyField('TalksUser', through='TalksUserCollection', blank=True)
    public = models.BooleanField(default=False)

    def _get_items_by_model(self, model):
        """Used when selecting a particular type (specified in the `model` arg)
        of objects from our Collection.

            1) Get the ContentType for that `model`
            2) Filter to the CollectionItems of that ContentType and get all
               `object_id`s
            3) Select these `object_id`s from the `model`
        """
        content_type = ContentType.objects.get_for_model(model)
        ids = self.collectionitem_set.filter(content_type=content_type
                                             ).values_list('object_id')
        return model.objects.filter(id__in=itertools.chain.from_iterable(ids))

    class ItemAlreadyInCollection(Exception):
        pass

    class InvalidItemType(Exception):
        pass

    def get_absolute_url(self):
        return reverse('view-list', args=[str(self.slug)])

    def get_api_url(self):
        return reverse('api-collection', args=[str(self.slug)])

    def get_ics_url(self):
        return reverse('api-collection-ics', args=[str(self.slug)])


    def save(self, *args, **kwargs):
        if not self.slug:
            # Newly created object, so set slug
            self.slug = str(uuid.uuid4())

        super(Collection, self).save(*args, **kwargs)

    def add_item(self, item):
        if isinstance(item, Event):
            # Adding an event
            content_type = ContentType.objects.get_for_model(Event)
        elif isinstance(item, EventGroup):
            # Adding event group
            content_type = ContentType.objects.get_for_model(EventGroup)
        elif isinstance(item, CollectedDepartment):
            # Adding department
            content_type = ContentType.objects.get_for_model(CollectedDepartment)
        else:
            raise self.InvalidItemType()
        try:
            self.collectionitem_set.get(content_type=content_type,
                                        object_id=item.id)
            raise self.ItemAlreadyInCollection()
        except CollectionItem.DoesNotExist:
            item = self.collectionitem_set.create(item=item)
            return item

    def remove_item(self, item):
        if isinstance(item, Event):
            content_type = ContentType.objects.get_for_model(Event)
        elif isinstance(item, EventGroup):
            content_type = ContentType.objects.get_for_model(EventGroup)
        elif isinstance(item, CollectedDepartment):
            content_type = ContentType.objects.get_for_model(CollectedDepartment)
        else:
            raise self.InvalidItemType()
        try:
            item = self.collectionitem_set.get(content_type=content_type,
                                               object_id=item.id)
            item.delete()
            return True
        except CollectionItem.DoesNotExist:
            return False

    def get_events(self):
        return self._get_items_by_model(Event)

    def get_event_groups(self):
        return self._get_items_by_model(EventGroup)

    def get_departments(self):
        return self._get_items_by_model(CollectedDepartment)

    def get_all_events(self):
        """
          Returns all distinct events in this collections events, event groups, and departments:
        """
        eventIDs = self.collectionitem_set.filter(content_type=ContentType.objects.get_for_model(Event)
                                             ).values_list('object_id')
        eventGroupIDs = self.collectionitem_set.filter(content_type=ContentType.objects.get_for_model(EventGroup)
                                             ).values_list('object_id')
        collectedDepartmentIDs = self.collectionitem_set.filter(content_type=ContentType.objects.get_for_model(CollectedDepartment)
                                             ).values_list('object_id')

        events = Event.objects.filter(id__in=itertools.chain.from_iterable(eventIDs))

        eventsInEventGroups = Event.objects.filter(group=eventGroupIDs)

        # get all department ids
        from talks.api.services import get_all_department_ids

        departments = CollectedDepartment.objects.filter(id__in=itertools.chain.from_iterable(collectedDepartmentIDs)).values('department')
        departmentIDs = [dep['department'] for dep in departments]
        allDepartmentIDs = get_all_department_ids(departmentIDs, True)
        departmentEvents = Event.objects.filter(department_organiser__in=allDepartmentIDs)

        allEvents = events | eventsInEventGroups | departmentEvents

        return allEvents.distinct().order_by('start')

    def contains_item(self, item):
        if isinstance(item, Event):
            content_type = ContentType.objects.get_for_model(Event)
        elif isinstance(item, EventGroup):
            content_type = ContentType.objects.get_for_model(EventGroup)
        elif isinstance(item, CollectedDepartment):
            content_type = ContentType.objects.get_for_model(CollectedDepartment)
        else:
            raise self.InvalidItemType()
        try:
            self.collectionitem_set.get(content_type=content_type,
                                        object_id=item.id)
            return True
        except CollectionItem.DoesNotExist:
            return False

    def contains_department(self, department_id):
        try:
            collectedDepartment = CollectedDepartment.objects.get(department=department_id)
        except CollectedDepartment.DoesNotExist:
            # This department hasn't been collected at all, so cannot be in any collection
            return False
        result = self.contains_item(collectedDepartment)
        return result

    def user_collection_permission(self, user):
        """
        :param user: The user accessing the collection
        :return: The role that user has on that collection (if any)
            ie.  owner, editor, reader or None.
        """
        talksuser = user if isinstance(user, TalksUser) else user.talksuser
        roles = self.talksusercollection_set.filter(user=talksuser).values_list('role', flat=True)
        role = None
        if COLLECTION_ROLES_OWNER.encode('utf-8') in roles:
            role = COLLECTION_ROLES_OWNER
        elif COLLECTION_ROLES_EDITOR in roles:
            role = COLLECTION_ROLES_EDITOR
        elif COLLECTION_ROLES_READER in roles:
            role = COLLECTION_ROLES_READER
        return role


    @property
    def description_html(self):
        return textile_restricted(self.description, auto_link=True, lite=False)

    def user_can_edit(self, user):
        return self.editor_set.filter(user_id=user.id, talksusercollection__role=COLLECTION_ROLES_OWNER).exists()

    def user_can_view(self, user):
        return self.editor_set.filter(user_id=user.id, talksusercollection__role__in=[COLLECTION_ROLES_OWNER, COLLECTION_ROLES_EDITOR, COLLECTION_ROLES_READER]).exists()

    def get_number_of_readers(self):
        """
        If this collection is public, return the number of users who have subscribed to this collection
        """
        return TalksUserCollection.objects.filter(collection=self, role=COLLECTION_ROLES_READER).count()

    def __unicode__(self):
        return self.title


class TalksUserCollection(models.Model):
    user = models.ForeignKey("TalksUser")
    collection = models.ForeignKey(Collection)
    role = models.TextField(choices=COLLECTION_ROLES, default=COLLECTION_ROLES_OWNER)
    is_main = models.BooleanField(default=False)
    class Meta:
        # For the admin interface where we only expose owner relationships for public lists
        verbose_name = "Public Collection Ownership"
        verbose_name_plural = "Public Collection Ownerships"

    def __unicode__(self):
        return unicode(self.user)


class TalksUser(models.Model):

    user = models.OneToOneField(User)
    collections = models.ManyToManyField(Collection, through=TalksUserCollection, blank=True)

    def save(self, *args, **kwargs):
        super(TalksUser, self).save(*args, **kwargs)
        if self.collections.count() == 0:
            default_collection = Collection.objects.create(title=DEFAULT_COLLECTION_NAME)
            # Link the collection to the user
            TalksUserCollection.objects.create(user=self,
                                            collection=default_collection,
                                            role=COLLECTION_ROLES_OWNER,
                                            is_main=True)

    def __unicode__(self):
        return unicode(self.user)


class CollectionItem(models.Model):

    collection = models.ForeignKey(Collection)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    # Currently item can be an Event or EventGroup, or a DepartmentCollection
    item = GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = [('collection', 'content_type', 'object_id')]


class DepartmentFollow(models.Model):
    pass


class LocationFollow(models.Model):
    pass

@receiver(models.signals.post_save, sender=User)
def ensure_profile_exists(sender, instance, created, **kwargs):
    """If the User has just been created we use a signal to also create a TalksUser
    """
    if created:
        tuser, tuser_created = TalksUser.objects.get_or_create(user=instance)
