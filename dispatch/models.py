import numpy as np
import datetime

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from .fields import CompressedJSONField
from .utils import to_dict

class CompressedJSONModel(models.Model):
    value = CompressedJSONField(null=False, default=b'')


# Create your models here.
class ThermalPlant(models.Model):
    # todo: toask: What does BSE, RMP, NRM, UPwarm, depreciation ... stand for?
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # production
    capacity = models.FloatField(blank=False, verbose_name='Capacity [MW]')
    efficiency = models.FloatField(blank=False, verbose_name='Efficiency [0-1]')
    MIN_prod_fraction = models.FloatField(blank=False, verbose_name='Minimal production fraction [0-1]')
    SEL_prod_fraction = models.FloatField(blank=False, verbose_name='Stable Export Limit production fraction [0-1]')
    MEL_prod_fraction = models.FloatField(blank=False, verbose_name='Maximal Export Limit production fraction [0-1]')

    # ramping
    ramping_rate_BSE = models.FloatField(blank=False, verbose_name='Ramping Rate BSE')
    ramping_rate_RMP = models.FloatField(blank=False, verbose_name='Ramping Rate RMP')
    ramping_rate_NRM = models.FloatField(blank=False, verbose_name='Ramping Rate NRM')

    ramping_costs_BSE = models.FloatField(blank=False, verbose_name='Ramping Costs BSE [0-1]')
    ramping_costs_RMP = models.FloatField(blank=False, verbose_name='Ramping Costs RMP [0-1]')
    ramping_costs_NRM = models.FloatField(blank=False, verbose_name='Ramping Costs NRM [0-1]')

    # costs
    depreciation = models.FloatField(blank=False, verbose_name='???')
    shutdown_costs = models.FloatField(blank=False, verbose_name='Costs of Shutdown [EUR/MW]')
    hot_start_costs = models.FloatField(blank=False, verbose_name='Costs of Hot Start [EUR/MW]')
    warm_start_costs = models.FloatField(blank=False, verbose_name='Costs of Warm Start [EUR/MW]')
    cold_start_costs = models.FloatField(blank=False, verbose_name='Costs of Cold Start [EUR/MW]')

    # start / stop
    hot_start_within_timedelta = models.FloatField(blank=False, verbose_name='Start counts as hot start if happening within X hours.')
    warm_start_within_timedelta = models.FloatField(blank=False, verbose_name='Start counts as warm start if happening within X hours.')

    # derived characteristics
    # implementation as functions?
    # todo: as a lot of values are just scaled by the capacity, maybe one can use dynamic methods that check if the
    # attribute doesn't exist if the attribute is a existing attribute + _MW in the end and then returns the value scaled
    # by the capacity. (Maybe not worth the effort as the plant models should stay fairly constant)
    ramping_rate_BSE_MW = models.FloatField(blank=False, verbose_name='Ramping Rate BSE [MW/time]')
    ramping_rate_RMP_MW = models.FloatField(blank=False, verbose_name='Ramping Rate RMP [MW/time]')
    ramping_rate_NRM_MW = models.FloatField(blank=False, verbose_name='Ramping Rate NRM [MW/time]')
    consumption = models.FloatField(blank=False, verbose_name='Consumption/Input [MW]')
    depreciation_MW = models.FloatField(blank=False, verbose_name='Depreciation of ??? [EUR/MW]')
    MIN = models.FloatField(blank=False, verbose_name='Minimal export limit [MW]')
    SEL = models.FloatField(blank=False, verbose_name='Stable export limit [MW]')
    MEL = models.FloatField(blank=False, verbose_name='Maximal export limit [MW]')
    UPhot_cost = models.FloatField(blank=False, verbose_name='UPhot_cost')
    UPwarm_cost = models.FloatField(blank=False, verbose_name='UPwarm_cost')
    UPcold_cost = models.FloatField(blank=False, verbose_name='UPcold_cost')
    UPhot_time = models.FloatField(blank=False, verbose_name='UPhot_time')
    UPwarm_time = models.FloatField(blank=False, verbose_name='UPwarm_time')
    DW_cost = models.FloatField(blank=False, verbose_name='DW_cost')

    def save(self, *args, **kwargs):
        # create derived fields
        self.ramping_rate_BSE_MW = self.ramping_rate_BSE * self.capacity
        self.ramping_rate_RMP_MW = self.ramping_rate_RMP * self.capacity
        self.ramping_rate_NRM_MW = self.ramping_rate_NRM * self.capacity
        self.consumption = self.capacity / self.efficiency
        self.depreciation_MW = self.depreciation * self.capacity
        self.MIN = self.MIN_prod_fraction * self.capacity
        self.SEL = self.SEL_prod_fraction * self.capacity
        self.MEL = self.MEL_prod_fraction * self.capacity
        self.UPhot_cost = self.hot_start_costs * self.capacity
        self.UPwarm_cost = self.warm_start_costs * self.capacity
        self.UPcold_cost = self.cold_start_costs * self.capacity
        self.UPhot_time = self.hot_start_within_timedelta
        self.UPwarm_time = self.warm_start_within_timedelta
        self.DW_cost = self.shutdown_costs * self.capacity

        # Call the "real" save() method.
        super().save(*args, **kwargs)

    def to_dict(self):
        return to_dict(self)


class TimeSeriesIndex(models.Model):
    """
    Indexes are UTC encoded series of date times.
    """
    INDEX_TYPE_CHOICES = (
        (1, _('integer')),
        (2, _('datetime')),
    )

    index_type = models.IntegerField(choices=INDEX_TYPE_CHOICES, default=1, blank=False)

    # datetime index
    datetime_start = models.DateTimeField(null=True)
    datetime_interval = models.DurationField(null=True)

    # todo: time index (just as time_start, time_interval instead of datetime)

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

    def _convert_data_index_to_model(self, index):
        if len(index) == 0:
            #todo: raise error
            assert len(index) > 0

        def is_integer_index(index):
            return type(index[0]) == int

        def is_datetime_index(index):
            return (type(index[0]) == datetime.datetime) or (type(index[0]) == np.datetime64)

        index_type = None
        index_types = {
            'integer': is_integer_index,
            'datetime': is_datetime_index
        }

        for t, f in index_types.items():
            if f(index):
                index_type = t

        # assuming that index is ordered
        start = index[0]

        # assuming that index is ordered and have equidistant spacing
        interval = -1
        if len(index) > 1:
            interval = index[1] - index[0]

        result = {
            'index_type': None,
            'integer_offset': None,
            'datetime_start': None,
            'datetime_interval': None
        }

        if index_type == 'integer':
            result['index_type'] = 1
            result['integer_offset'] = start

        elif index_type == 'datetime':
            result['index_type'] = 2
            result['datetime_start'] = start
            result['datetime_interval'] = interval

        return result

    def create_from_data(self, index):
        """
        Assumes index is ordered.
        :param index:
        :return:
        """

        index_dict = self._convert_data_index_to_model(index)

        self.index_type = index_dict['index_type']
        if index_dict['index_type'] == 1:
            self.integer_offset = index_dict['integer_offset']

        elif index_dict['index_type'] == 2:
            self.datetime_start = index_dict['datetime_start']
            self.datetime_interval = index_dict['datetime_interval']

        return self

    def does_exist(self, index):
        """
        Looks up if an index representation for a data index already exist.
        :param index:
        :return: Model instance of TimeSeriesIndex if exists
        """

        index_dict = self._convert_data_index_to_model(index)

        index_dict = {key:value for (key, value) in index_dict.items() if value is not None}

        # delete None
        try:
            model_instance = TimeSeriesIndex.objects.get(**index_dict)
            return model_instance

        except TimeSeriesIndex.DoesNotExist:
            return None


class TimeSeries(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) # reference to creat
    name = models.CharField(max_length=256) #
    description = models.TextField(default='') #

    index = models.ForeignKey(TimeSeriesIndex, on_delete=models.CASCADE)   # self reference
    data = CompressedJSONField(null=False, default=b'') # list of values, maybe binary and zipped
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


def create_thermal_plant_dispatch_model(version, plant, wholesale_price, clean_fuel_price, time_series_index, pk=None):
    """
    Create instance or edit it if pk is provided.
    :param version:
    :param plant:
    :param wholesale_price:
    :param clean_fuel_price:
    :param time_series_index:
    :param pk:
    :return:
    """
    if pk is None:
        model_instance = ThermalPlantDispatch()

    else:
        #todo: maybe use get_object_or_404
        model_instance = ThermalPlantDispatch.objects.get(pk=pk)

    # create time series index if it doesn't exist already
    if len(time_series_index) == 0:
        # todo: raise error
        pass

    def is_integer_index(index):
        return type(index[0]) == int

    def is_datetime_index(index):
        return (type(index[0]) == datetime.datetime) or (type[index[0]] == np.datetime64)

    check_type_of_index = {
        'integer': is_integer_index,
        'datetime': is_datetime_index
    }



class ThermalPlantDispatch(models.Model):
    # todo: maybe call differently to reflect purpose of Object. ThermalPlantDispatchSetup
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

    def save(self, *args, **kwargs):
        """

        :return:
        """

        # prepare all the foreign relationship if the model is saved the first time
        print(self.pk)
        if self.pk is None:
            print('here')


        # Call the "real" save() method.
        super().save(*args, **kwargs)