rm "*/migrations"
$FileName = "test.db.sqlite3"
if (Test-Path $FileName) {
  Remove-Item $FileName
}
py manage.py makemigrations experiments
py manage.py makemigrations users
py manage.py migrate
py manage.py loaddata status
py manage.py loaddata request_status
py manage.py loaddata achievement
$env:DJANGO_SUPERUSER_USERNAME="admin"
$env:DJANGO_SUPERUSER_PASSWORD="admin"
py manage.py createsuperuser --noinput --email "test@example.com"
py manage.py create_groups
py manage.py create_testusers