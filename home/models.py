from django.db import models
import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler


class FileModel(models.Model):
    name = models.CharField(max_length=200)
    length = models.FloatField()
    status = models.FloatField()
    converted_name = models.CharField(max_length=200, null=True)
    created = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.name


'''
scheduled job to remove old files
'''
scheduler = BackgroundScheduler()


def check_oldfiles():
    filelist = FileModel.objects.all()
    now = datetime.now()
    for item in filelist:
        naive = item.created.replace(tzinfo=None)
        duration = now - naive
        if duration.total_seconds() > 1800:
            if item.name and os.path.exists(item.name):
                os.remove(item.name)
            if item.converted_name and os.path.exists(item.converted_name):
                os.remove(item.converted_name)
            item.delete()


scheduler.add_job(check_oldfiles, 'interval', seconds=60)
try:
    scheduler.start()
except:
    pass