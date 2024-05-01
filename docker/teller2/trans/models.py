from django.db import models
from django.contrib.auth.models import User	  

# Payment method---
class PmethodGroup(models.Model):
    name = models.CharField(max_length=200)
    order = models.IntegerField(default=0)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    
    
class Pmethod(models.Model):
    name = models.CharField(max_length=200)
    group = models.ForeignKey(PmethodGroup, on_delete=models.CASCADE)
    #    group = models.ForeignKey(PmethodGroup, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    


# category---
class CategoryGroup(models.Model):
    name = models.CharField(max_length=200)
    order = models.IntegerField(default=0)
    
class Category(models.Model):
    name = models.CharField(max_length=200)
    group = models.ForeignKey(CategoryGroup, on_delete=models.PROTECT)
    order = models.IntegerField(default=0)
    

SHARE_TYPES = (
    (1, 'OWN'),
    (2, 'SHARE'),
    (3, 'PAY4OTHER'),
)
    
class Trans(models.Model):
    date = models.DateTimeField('date')
    name = models.CharField(max_length=200)
    expense = models.IntegerField(default=0)
    balance = models.IntegerField(default=0)
    memo = models.CharField(max_length=1000)

    pmethod = models.ForeignKey(Pmethod, on_delete=models.PROTECT)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)

    user = models.ForeignKey(User, on_delete=models.PROTECT)

    share_type = models.IntegerField(choices=SHARE_TYPES)
    # pay for who?
    user_pay4 = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+', null=True)

    # Is it already clearance
    #fclearance = models.BooleanField(default=False)
    #fClearance = models.BooleanField(default=False)

    includebalance = models.BooleanField(default=True)
    includemonthlysum = models.BooleanField(default=True)



    


