# Generated by Django 2.1.1 on 2018-09-16 09:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0009_auto_20180916_1124'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lefinstance',
            name='solved_by',
            field=models.CharField(max_length=8, null=True),
        ),
    ]
