# Generated by Django 3.2.17 on 2023-02-11 15:03

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0003_remove_user_name_user_first_name_user_last_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="first_name",
            field=models.CharField(max_length=150, verbose_name="first name"),
        ),
    ]