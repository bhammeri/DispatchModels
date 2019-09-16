import numpy as np

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


# Create your models here.
class ThermalPlant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    capacity = models.FloatField(null=False)


class TimeSeriesIndex(models.Model):
    """
    Indexes are UTC encoded series of date times.
    """
    INDEX_TYPE_CHOICES = (
        (1, _('integer index')),
        (2, _('datetime index')),
    )

    index_type = models.IntegerField(choices=INDEX_TYPE_CHOICES, default=1, blank=False)

    # datetime index
    datetime_start = models.DateTimeField(null=True)
    datetime_interval = models.DurationField(null=True)

    # integer index
    integer_offset = models.IntegerField(null=True, default=0)  # integer offset

    # constraints: make sure that interval is positive

    def create_index(self, length):
        """
        Creates an numpy array as index for a time series. Either integer or datetime.
        :param length: Number of items in the index.
        :return:
        """
        # create a numpy array as basis for the index
        result = np.arange(length)

        # if integer index
        if self.index_type == 1:
            result += self.integer_offset

        # datetime index
        elif self.index_type == 2:
            result = self.datetime_start + self.datetime_interval * result

        return result


class TimeSeries(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) # reference to creat
    name = models.CharField(max_length=256) #
    description = models.TextField(default='') #

    index = models.ForeignKey(TimeSeriesIndex, on_delete=models.CASCADE)   # self reference
    data = models.BinaryField(null=False, default=b'') # list of values, maybe binary and zipped
    length = models.IntegerField(null=False, default=0) # store length of data, to be able to easily create index

    pub_date = models.DateTimeField('date published', auto_now_add=True, null=False)
    last_altered = models.DateTimeField('date altered', auto_now=True, null=False)
    public = models.BooleanField(default=False)

    def create_index(self):
        """
        Creates an index for time series
        :return:
        """

        result = self.index.create_index(self.length)

        return result


class ThermalPlantDispatch(models.Model):
    """
    The setup for a thermal plant dispatch simulation.
    """
    version = models.IntegerField(default=0)
    plant = models.ForeignKey(ThermalPlant, on_delete=models.CASCADE)
    wholesale_price = models.ForeignKey(TimeSeries,
                                        on_delete=models.CASCADE,
                                        related_name='dispatch_wholesale_price_set')
    clean_fuel_price = models.ForeignKey(TimeSeries,
                                         on_delete=models.CASCADE,
                                         related_name='dispatch_clean_fuel_price_set')

    # todo: decide if this model also should reference the TimeSeriesIndex (for convenience?)
    time_series_index = models.ForeignKey(TimeSeriesIndex, on_delete=models.CASCADE)

    # todo: make sure that all time series use the same TimeSeriesIndex