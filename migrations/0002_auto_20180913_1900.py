# Generated by Django 2.1.1 on 2018-09-13 17:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=8)),
            ],
        ),
        migrations.AddField(
            model_name='player',
            name='token',
            field=models.CharField(default='-1', max_length=8),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='room',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.Player'),
        ),
    ]
