from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0008_run_number'),
    ]

    operations = [
        migrations.RenameField('experiment', 'action_file', 'playbook_file'),
        migrations.RenameField('experiment', 'sha256action', 'sha256playbook'),
        migrations.RemoveField('experiment', 'testset_file'),
        migrations.RemoveField('experiment', 'sha256testset'),
    ]
