from django.db import models

class PmethodGroup(models.Model):
    name = models.CharField(max_length=200)
    order = models.IntegerField(default=0)

    
# Payment method    
class Pmethod(models.Model):
    name = models.CharField(max_length=200)
    group = models.ForeignKey(PmethodGroup, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    

class Trans(models.Model):
    date = models.DateTimeField('date')
    name = models.CharField(max_length=200)
    expense = models.IntegerField(default=0)
    balance = models.IntegerField(default=0)

    memo = models.CharField(max_length=1000)

    pmethod = models.ForeignKey(Pmethod, on_delete=models.CASCADE)

    


