# Generated by Django 2.1.1 on 2018-09-16 09:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0010_auto_20180916_1124'),
    ]

    operations = [
        migrations.AddField(
            model_name='lefinstance',
            name='solution',
            field=models.CharField(default=None, max_length=13),
            preserve_default=False,
        ),
    ]
