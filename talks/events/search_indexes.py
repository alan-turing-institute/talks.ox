from __future__ import absolute_import
from haystack import indexes

from .models import Event
from talks.events.models import EVENT_IN_PREPARATION, EVENT_PUBLISHED


class EventIndex(indexes.SearchIndex, indexes.Indexable):
    # text: multiple fields use to do full-text search
    text = indexes.MultiValueField(document=True, stored=False)

    title = indexes.CharField(model_attr='title')
    description = indexes.CharField(model_attr='description', null=True)
    slug = indexes.CharField(model_attr='slug', null=False)
    start = indexes.DateTimeField(model_attr='start', faceted=True)
    speakers = indexes.MultiValueField(faceted=True, null=True)
    department = indexes.CharField(faceted=True, null=True)
    location = indexes.CharField(faceted=True, null=True)
    topics = indexes.MultiValueField(faceted=True, null=True)
    is_published = indexes.BooleanField(null=False)
    is_cancelled = indexes.BooleanField(null=False)
    group = indexes.CharField(faceted=True, null=True)
    group_slug = indexes.CharField(null=True)
    lists = indexes.MultiValueField(faceted=True, null=True)


    def get_model(self):
        return Event

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        #return self.get_model().objects.filter(pub_date__lte=datetime.datetime.now())
        return self.get_model().objects.all()

    def prepare(self, obj):
        """Overriding the prepare() method of SearchIndex in order to add our most complicated fields
        It is done in prepare() rather than the individual prepare_FIELD() to avoid having to do
        multiple calls to the APIs...
        """
        self.prepared_data = super(EventIndex, self).prepare(obj)

        topics = obj.api_topics
        topics_pref_labels = []
        topic_alt_labels = []
        if topics:
            for topic in topics:
                topics_pref_labels.append(topic.get('prefLabel', ''))
                topic_alt_labels.extend(topic.get('altLabels', []))
        if obj.department_organiser:
            api_dept = obj.api_organisation
        else:
            api_dept = None
        if obj.location:
            api_loc = obj.api_location
        else:
            api_loc = None
        speakers_names = [speaker.name for speaker in obj.speakers.all()]

        # Speakers
        self.prepared_data[self.speakers.index_fieldname] = speakers_names

        # Department organiser
        if api_dept:
            self.prepared_data[self.department.index_fieldname] = api_dept.get('name', '')

        # Location
        if api_loc:
            self.prepared_data[self.location.index_fieldname] = api_loc.get('name', '')

        # Topics
        if topics_pref_labels:
            self.prepared_data[self.topics.index_fieldname] = topics_pref_labels

        # Published status
        self.prepared_data[self.is_published.index_fieldname] = obj.is_published
        self.prepared_data[self.is_cancelled.index_fieldname] = obj.is_cancelled

        # Series name
        if obj.group:
            self.prepared_data[self.group.index_fieldname] = obj.group.title
            self.prepared_data[self.group_slug.index_fieldname] = obj.group.slug

        # lists
        lists_names = [list.title for list in obj.public_collections_containing_this_event.all()]
        self.prepared_data[self.lists.index_fieldname] = lists_names

        full_text_content = []      # used when searching full text

        if obj.title:
            full_text_content.append(obj.title)
        if obj.description:
            full_text_content.append(obj.description)
        if topics_pref_labels:
            full_text_content.extend(topics_pref_labels)
        if topic_alt_labels:
            full_text_content.extend(topic_alt_labels)
        if obj.group:
            full_text_content.append(obj.group.title)

        full_text_content.extend(speakers_names)

        full_text_content.extend(lists_names)

        self.prepared_data[self.text.index_fieldname] = full_text_content

        return self.prepared_data
