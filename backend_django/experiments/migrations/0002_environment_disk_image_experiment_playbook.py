from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0001_initial'),
    ]

    operations = [
        # Environment: remove vagrantbox, add disk image fields
        migrations.RemoveField(
            model_name='environment',
            name='vagrantbox',
        ),
        migrations.AddField(
            model_name='environment',
            name='hypervisor',
            field=models.CharField(default='qemu', max_length=50),
        ),
        migrations.AddField(
            model_name='environment',
            name='disk_image_url',
            field=models.URLField(blank=True, max_length=2000, null=True),
        ),
        migrations.AddField(
            model_name='environment',
            name='disk_image_sha256',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='environment',
            name='disk_image_format',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),

        # Experiment: rename action_file -> playbook_file, remove testset_file
        migrations.RenameField(
            model_name='experiment',
            old_name='action_file',
            new_name='playbook_file',
        ),
        migrations.RemoveField(
            model_name='experiment',
            name='testset_file',
        ),
        migrations.RenameField(
            model_name='experiment',
            old_name='sha256action',
            new_name='sha256playbook',
        ),
        migrations.RemoveField(
            model_name='experiment',
            name='sha256testset',
        ),
    ]
