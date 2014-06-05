from django.db import models
from django.contrib.auth.models import User
from dateutil.rrule import *
from datetime import datetime, timedelta
from django.utils.timezone import utc
import pickle

# Create your models here.

FREQUENCY_CHOICES = (
    ('YEARLY','yearly'),
    ('MONTHLY','monthly'),
    ('WEEKLY','weekly'),
    ('DAILY','daily'),
)

class RecurrenceRule(models.Model):
    '''
    This class stores an rrule object from python-dateutil as a django model for saving to the database. 
    '''
    name = models.CharField(max_length=36)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    params = models.BinaryField(blank=True)
    def get_params(self):
        if self.params:
            return pickle.loads(self.params)

    def save(self, *args, **kwargs):
        if self.params:
            self.params = pickle.dumps(self.params)
        super(RecurrenceRule, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name

class Event(models.Model):
    '''
    This class defines a calendar event instance, which may be one-time or recurring via ForeignKey relation to a RecurrenceRule object
    '''
    name = models.CharField(max_length=36)
    creator = models.ForeignKey(User)
    rule = models.ForeignKey(RecurrenceRule, blank=True, null=True)
    startdatetime = models.DateTimeField(default=datetime.now(utc))
    enddatetime = models.DateTimeField(default=datetime.now(utc)+timedelta(hours=1))

    def get_recurrence_rule(self):
        '''
        Returns the dateutil.rrule object instance associated with this Event
        '''
        if self.rule:
            return rrule(eval(self.rule.frequency), dtstart=self.startdatetime, **self.rule.get_params())
        return None

    def get_occurrences(self, start, end):
        '''
        Accepts start and end datetime objects and returns a list of datetime objects that fall between the start and end date arguments
        according to this event's rrule instance.
        TODO: return both calculated recurrence dates and persistent Occurrence objects.
        '''
        rule = self.get_recurrence_rule()
        return rule.between(start, end, inc=True)

class Occurrence(models.Model):
    '''
    Persists an occurrence instance of a recurring event to the database so that other objects can be associated to an occurrence.
    '''
    event = models.ForeignKey(Event)