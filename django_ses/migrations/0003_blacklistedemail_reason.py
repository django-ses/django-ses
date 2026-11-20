from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("django_ses", "0002_blacklistedemail"),
    ]

    operations = [
        migrations.AddField(
            model_name="blacklistedemail",
            name="reason",
            field=models.TextField(blank=True, default=""),
        ),
    ]
