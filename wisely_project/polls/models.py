from django.db import models
from django.utils import timezone


class Question(models.Model):
    question_text = models.CharField(max_length=2000)
    pub_date = models.DateTimeField('date published', default=timezone.now())
    allow_custom = models.BooleanField(default=False)
    allow_multiple = models.BooleanField(default=False)

    def only_custom(self):
        return self.choice_set.filter(custom=False) == 0

    def __unicode__(self):
        return self.question_text


class Choice(models.Model):
    question = models.ForeignKey(Question)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    custom = models.BooleanField(default=False)

    def __unicode__(self):
        return self.choice_text