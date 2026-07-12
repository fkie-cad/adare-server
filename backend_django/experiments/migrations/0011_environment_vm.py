from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0010_delete_requestcreationmessage'),
    ]

    operations = [
        migrations.AddField(
            model_name='environment',
            name='vm',
            field=models.CharField(blank=True, default='', max_length=2000),
        ),
    ]
