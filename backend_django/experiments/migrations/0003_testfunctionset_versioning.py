from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0002_environment_disk_image_experiment_playbook'),
    ]

    operations = [
        # Remove unique constraint on name (will use name+version instead)
        migrations.AlterField(
            model_name='testfunctionset',
            name='name',
            field=models.CharField(max_length=100),
        ),
        # Add version field
        migrations.AddField(
            model_name='testfunctionset',
            name='version',
            field=models.IntegerField(default=1),
        ),
        # Add unique constraint on (name, version)
        migrations.AddConstraint(
            model_name='testfunctionset',
            constraint=models.UniqueConstraint(fields=['name', 'version'], name='unique_tf_version'),
        ),
    ]
