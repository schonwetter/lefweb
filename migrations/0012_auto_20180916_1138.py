# Generated by Django 2.1.1 on 2018-09-16 09:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0011_lefinstance_solution'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lefinstance',
            name='solution',
            field=models.CharField(max_length=13, null=True),
        ),
    ]