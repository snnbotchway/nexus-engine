# Generated by Django 4.1.7 on 2023-02-28 01:50

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0003_follow_follow_unique_follow_follow_no_self_follow"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="follows",
            field=models.ManyToManyField(
                related_name="followed_by",
                through="profiles.Follow",
                to="profiles.profile",
            ),
        ),
    ]
