import numpy as np

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _




# Create your models here.
class ThermalPlant(models.Model):
    # todo: toask: What does BSE, RMP, NRM, stand for?
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # production
    capacity = models.FloatField(blank=False, verbose_name='Capacity [MW]')
    efficiency = models.FloatField(blank=False, verbose_name='Efficiency [0-1]')
    MIN_prod_fraction = models.FloatField(blank=False, verbose_name='Minimal production fraction [0-1]')
    SEL_prod_fraction = models.FloatField(blank=False, verbose_name='Stable Export Limit production fraction [0-1]')
    MEL_prod_fraction = models.FloatField(blank=False, verbose_name='Maximal Export Limit production fraction [0-1]')

    # ramping
    ramping_rate_BSE = models.Floatfield(blank=False, verbose_name='Ramping Rate BSE')
    ramping_rate_RMP = models.FloatField(blank=False, verbose_name='Ramping Rate RMP')
    ramping_rate_NRM = models.FloatField(blank=False, verbose_name='Ramping Rate NRM')

    ramping_costs_BSE = models.FloatField(blank=False, verbose_name='Ramping Costs BSE')
    ramping_costs_RMP = models.FloatField(blank=False, verbose_name='Ramping Costs RMP')
    ramping_costs_NRM = models.FloatField(blank=False, verbose_name='Ramping Costs NRM')

    # costs
    depreciation = models.FloatField(blank=False, verbose_name='???')
    shutdown_costs = models.FloatField(blank=False, verbose_name='Costs of Shutdown [EUR/MW]')
    warm_start_costs = models.FloatField(blank=False, verbose_name='Costs of Warm Start [EUR/MW]')
    cold_start_costs = models.FloatField(blank=False, verbose_name='Costs of Cold Start [EUR/MW]')
    # start / stop
    hot_start_within_timedelta = models.Floatfield(blank=False, verbose_name='Start counts as hot start if happening within X hours.')
    warm_start_within_timedelta = models.FloatField(blank=False, verbose_name='Start counts as warm start if happening within X hours.')

    # derived characteristics
    ramping_rate_MW_BSE  # (x, y * self.MW_installed)
    ...

    self_consumption    # self.n_consumption = self.MW_installed / self.n_efficiency
    depreciation_MW     # self.depriciation = depriciation * self.MW_installed

    self.MIN = MIN_fraction * self.MW_installed
    self.SEL = SEL_fraction * self.MW_installed
    self.MEL = MEL_fraction * self.MW_installed

    self.UPhot_cost = hot_start_cost * self.MW_installed
    self.UPwarm_cost = warm_start_cost * self.MW_installed
    self.UPcold_cost = cold_start_cost * self.MW_installed

    self.UPhot_time = hotStartWithinTime ???
    self.UPwarm_time = warmStartWithinTime ???
    self.DW_cost = shutdown_cost * self.MW_installed

class Plant:
    def __init__(self,
                 MW_installed,
                 efficiency,
                 rampingRates,
                 rampingCosts,
                 MIN_fraction,
                 SEL_fraction,
                 MEL_fraction,

                 depriciation,
                 shutdown_cost,
                 hot_start_cost,
                 warm_start_cost,
                 cold_start_cost,
                 hotStartWithinTime,
                 warmStartWithinTime,
                 ):
        self.MW_installed = MW_installed

        self.n_efficiency = efficiency

        self.n_production = self.MW_installed
        self.n_consumption = self.MW_installed / self.n_efficiency

        rampingRates.update((x, y * self.MW_installed) for x, y in rampingRates.items())
        self.rampingRates = rampingRates

        self.rampingCosts = rampingCosts

        self.depriciation = depriciation * self.MW_installed

        self.MIN = MIN_fraction * self.MW_installed
        self.SEL = SEL_fraction * self.MW_installed
        self.MEL = MEL_fraction * self.MW_installed

        self.UPhot_cost = hot_start_cost * self.MW_installed
        self.UPwarm_cost = warm_start_cost * self.MW_installed
        self.UPcold_cost = cold_start_cost * self.MW_installed

        self.UPhot_time = hotStartWithinTime
        self.UPwarm_time = warmStartWithinTime
        self.DW_cost = shutdown_cost * self.MW_installed


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