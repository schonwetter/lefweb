# Generated by Django 2.1.1 on 2018-09-16 09:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0008_auto_20180915_1251'),
    ]

    operations = [
        migrations.AddField(
            model_name='lefinstance',
            name='solved_by',
            field=models.CharField(default=None, max_length=8),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='lefinstance',
            name='time_to_solution',
            field=models.IntegerField(default=0),
        ),
    ]
