from django.db import models

class protectedValueError(Exception):
    def __init__(self, msg):
        super(protectedValueError, self).__init__(msg)


class timeStampManager(models.Manager):
    def __init__(self, *args, **kwargs):
        self.alive_only = kwargs.pop('alive_only', True)
        super(timeStampManager, self).__init__(*args, **kwargs)

    def get_queryset(self):
        if self.alive_only:
            return timeStampQuerySet(self.model).filter(delete_field="no")
        return timeStampQuerySet(self.model)

    def hard_delete(self):
        return self.get_queryset().hard_delete()


class timeStampQuerySet(models.QuerySet):
    def delete(self):
        for item in self:
            item.delete()
        return super(timeStampQuerySet, self)

    def hard_delete(self):
        return super(timeStampQuerySet, self).delete()

    def alive(self):
        return self.filter(delete_field="no")

    def dead(self):
        return self.filter(delete_field="yes")


class timeStamp(models.Model):
    """
	Description: This models is an abstract class that defines the columns that should be present in every table.
	"""
    created_date = models.DateTimeField(auto_now=True)
    delete_field = models.CharField(max_length=10, default="no")
    objects = timeStampManager()
    default_objects = models.Manager()

    class Meta:
        abstract = True