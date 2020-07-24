# Generated by Django 2.0.13 on 2020-07-21 13:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.DateTimeField()),
                ('end', models.DateTimeField()),
                ('title', models.CharField(blank=True, max_length=250)),
                ('title_not_announced', models.BooleanField(default=False, verbose_name='Title to be announced')),
                ('slug', models.SlugField()),
                ('description', models.TextField(blank=True)),
                ('various_speakers', models.BooleanField(default=False, verbose_name='Various Speakers')),
                ('audience', models.TextField(default='oxonly', verbose_name='Who can attend')),
                ('booking_type', models.TextField(choices=[('nr', 'Not required'), ('re', 'Required'), ('rc', 'Recommended')], default='nr', verbose_name='Booking required')),
                ('booking_url', models.URLField(blank=True, default='', verbose_name='Web address for booking')),
                ('booking_email', models.EmailField(blank=True, default='', max_length=254, verbose_name='Email address for booking')),
                ('cost', models.TextField(blank=True, default='', help_text='If applicable', verbose_name='Cost')),
                ('status', models.TextField(choices=[('preparation', 'In preparation'), ('published', 'Published'), ('cancelled', 'Cancelled')], default='published', verbose_name='Status')),
                ('embargo', models.BooleanField(default=False, verbose_name='Embargo')),
                ('special_message', models.TextField(blank=True, default='', help_text='Use this for important notices - e.g.: cancellation or a last minute change of venue', verbose_name='Special message')),
                ('location', models.TextField(blank=True)),
                ('location_details', models.TextField(blank=True, default='', help_text='e.g.: room number or accessibility information', verbose_name='Venue details')),
                ('department_organiser', models.TextField(blank=True, default='')),
                ('organiser_email', models.EmailField(blank=True, default='', max_length=254, verbose_name='Contact email')),
                ('editor_set', models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='EventGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=250)),
                ('slug', models.SlugField()),
                ('description', models.TextField(blank=True)),
                ('group_type', models.CharField(blank=True, choices=[('SE', 'Seminar Series'), ('CO', 'Conference')], default='SE', max_length=2, null=True)),
                ('occurence', models.TextField(blank=True, default='', help_text='e.g.: Mondays at 10 or September 19th to 20th.', verbose_name='Timing')),
                ('web_address', models.URLField(blank=True, default='', verbose_name='Web address')),
                ('department_organiser', models.TextField(blank=True, default='', verbose_name='Organising Department')),
                ('editor_set', models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=250)),
                ('lastname', models.CharField(blank=True, max_length=250)),
                ('slug', models.SlugField()),
                ('bio', models.TextField(blank=True, null=True, verbose_name='Affiliation')),
                ('email_address', models.EmailField(blank=True, max_length=254, null=True)),
                ('web_address', models.URLField(blank=True, null=True, verbose_name='Web address')),
            ],
        ),
        migrations.CreateModel(
            name='PersonEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('affiliation', models.TextField(blank=True)),
                ('role', models.TextField(choices=[('speaker', 'Speaker'), ('host', 'Host'), ('organiser', 'Organiser')], default='speaker')),
                ('url', models.URLField(blank=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='events.Event')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='events.Person')),
            ],
        ),
        migrations.CreateModel(
            name='TopicItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uri', models.URLField(db_index=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
            ],
        ),
        migrations.AddField(
            model_name='eventgroup',
            name='organisers',
            field=models.ManyToManyField(blank=True, null=True, to='events.Person'),
        ),
        migrations.AddField(
            model_name='event',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='events', to='events.EventGroup'),
        ),
        migrations.AddField(
            model_name='event',
            name='person_set',
            field=models.ManyToManyField(blank=True, through='events.PersonEvent', to='events.Person'),
        ),
        migrations.AlterUniqueTogether(
            name='topicitem',
            unique_together={('uri', 'content_type', 'object_id')},
        ),
    ]