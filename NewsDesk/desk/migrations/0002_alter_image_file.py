# Generated by Django 5.1.1 on 2024-09-30 18:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('desk', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='file',
            field=models.ImageField(upload_to='desk/files/images/', verbose_name='Изображение'),
        ),
    ]
