import numpy as np
import datetime
import pandas as pd
import uuid
import csv

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.db.models.fields.related import RelatedField
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator

from .fields import CompressedJSONField
from .utils import to_dict


class CompressedJSONModel(models.Model):
    value = CompressedJSONField(null=False, default=b'')


# Create your models here.
class ThermalPlant(models.Model):
    # todo: toask: What does BSE, RMP, NRM, UPwarm, depreciation ... stand for?
    # todo: validation of fields: >0, <1, MEL > SEL (form validation)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(blank=False, max_length=256, default='Plant', verbose_name='Plant name')
    pub_date = models.DateTimeField(auto_now_add=True)
    last_altered = models.DateTimeField(auto_now=True)

    # production
    capacity = models.FloatField(blank=False, verbose_name='Capacity [MW]', validators=[MinValueValidator(0)])
    efficiency = models.FloatField(blank=False, verbose_name='Efficiency [0-1]', validators=[MinValueValidator(0), MaxValueValidator(1)])
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
    depreciation = models.FloatField(blank=False, verbose_name='Depreciation [EUR/MW]')
    shutdown_costs = models.FloatField(blank=False, verbose_name='Costs of Shutdown [EUR/MW]')
    hot_start_costs = models.FloatField(blank=False, verbose_name='Costs of Hot Start [EUR/MW]')
    warm_start_costs = models.FloatField(blank=False, verbose_name='Costs of Warm Start [EUR/MW]')
    cold_start_costs = models.FloatField(blank=False, verbose_name='Costs of Cold Start [EUR/MW]')

    # start / stop
    hot_start_within_timedelta = models.FloatField(blank=False,
                                                   verbose_name='Start counts as hot start if happening within X hours.')
    warm_start_within_timedelta = models.FloatField(blank=False,
                                                    verbose_name='Start counts as warm start if happening within X hours.')

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
        result = to_dict(self)

        return result

    def __str__(self):
        return self.name


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
            # todo: raise error
            assert len(index) > 0

        def is_integer_index(index):
            return (type(index[0]) == int) or (type(index[0]) == np.int64)

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

        print('index_dict', index, index_dict)

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

        index_dict = {key: value for (key, value) in index_dict.items() if value is not None}

        # delete None
        try:
            model_instance = TimeSeriesIndex.objects.get(**index_dict)
            return model_instance

        except TimeSeriesIndex.DoesNotExist:
            return None

    def create_if_not_exists(self, index):
        result = self.does_exist(index)

        print('does_exist', result)

        if result is not None:
            return result
        else:
            return self.create_from_data(index)


class TimeSeries(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # reference to creat
    name = models.CharField(max_length=256)  #
    description = models.TextField(default='')  #

    index = models.ForeignKey(TimeSeriesIndex, on_delete=models.CASCADE)  # self reference
    data = CompressedJSONField(null=False, default=b'')  # list of values, maybe binary and zipped
    length = models.IntegerField(null=False, default=0)  # store length of data, to be able to easily create index
    unit = models.CharField(max_length=124, default='')

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

    def create_from_data(self, user, data, index=None):
        """
        Create from data.
        :param data:
        :param index:
        :return:
        """

        # todo: write test

        # if no index is given create an integer index
        if index is None:
            index = [item for item in range(len(data))]

        # create index if it does not exist already
        time_series_index = TimeSeriesIndex().create_if_not_exists(index)

    def to_dataframe(self):
        """
        Return a dataframe with index.
        :return:
        """

        # todo: write test

        index = self.create_index()

        df = pd.DataFrame({'index': index, self.name: self.data})

        df.set_index('index', inplace=True)

        return df


def create_thermal_plant_dispatch_model(user, version, plant_definition, time_series_index_data, wholesale_price,
                                        clean_fuel_price, pk=None):
    """
    Create instance or edit it if pk is provided.
    :param version:
    :param plant_definition: Dictionary containing all information about a plant definition.
    :param wholesale_price:
    :param clean_fuel_price:
    :param time_series_index:
    :param pk:
    :return:
    """
    # todo: function needs to be able to receive raw definitions/data or pks of already created objects. create asserts

    assert len(time_series_index_data) == len(wholesale_price) == len(
        clean_fuel_price), 'Time series data and index must have the same length.'

    if pk is None:
        model_instance = ThermalPlantDispatch()

    else:
        # todo: maybe use get_object_or_404
        model_instance = ThermalPlantDispatch.objects.get(pk=pk)

    # create time series index if it doesn't exist already
    time_series_index = TimeSeriesIndex().create_if_not_exists(time_series_index_data)
    time_series_index.save()

    print(time_series_index.pk)

    # create the two time series
    # 1. wholesale price
    wholesale_price_time_series = TimeSeries.objects.create(
        user=user,
        name='wholesale_price',
        description='',
        index=time_series_index,
        data=wholesale_price,
        length=len(wholesale_price),
        unit='EUR/MWh',
    )

    print('wholesale_price_time_series', wholesale_price_time_series.pk)

    # 2. clean fuel price
    clean_fuel_price_time_series = TimeSeries.objects.create(
        user=user,
        name='clean_fuel_price',
        description='',
        index=time_series_index,
        data=clean_fuel_price,
        length=len(clean_fuel_price),
        unit='EUR/MWh_thermal',
    )

    print('clean_fuel_price_time_series', clean_fuel_price_time_series.pk)

    # create plant
    # delete 'user' from plant_definition if exists
    if 'user' in plant_definition:
        del plant_definition['user']

    if 'id' in plant_definition:
        del plant_definition['id']

    # todo: only create if it does not exist already
    thermal_plant = ThermalPlant.objects.create(user=user, **plant_definition)

    print('thermal_plant', thermal_plant.pk)

    thermal_plant_dispatch_setup = ThermalPlantDispatch.objects.create(
        user=user,
        version=version,
        plant=thermal_plant,
        wholesale_price=wholesale_price_time_series,
        clean_fuel_price=clean_fuel_price_time_series,
        time_series_index=time_series_index,
    )

    return thermal_plant_dispatch_setup


class ThermalPlantDispatch(models.Model):
    # todo: maybe call differently to reflect purpose of Object. ThermalPlantDispatchSetup
    """
    The setup for a thermal plant dispatch simulation.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    version = models.IntegerField(default=0)
    plant = models.ForeignKey(ThermalPlant, on_delete=models.CASCADE)
    wholesale_price = models.ForeignKey(TimeSeries,
                                        on_delete=models.CASCADE,
                                        related_name='dispatch_wholesale_price_set')
    clean_fuel_price = models.ForeignKey(TimeSeries,
                                         on_delete=models.CASCADE,
                                         related_name='dispatch_clean_fuel_price_set')

    time_series_index = models.ForeignKey(TimeSeriesIndex, on_delete=models.CASCADE)

    def time_series(self):
        """
        Creates one common DataFrame for all data.
        :return:
        """

        # todo: write test

        # find all TimeSeries fields
        time_series_fields = []
        for field in self._meta.get_fields():
            if isinstance(field, RelatedField):
                if field.related_model is TimeSeries:  # weirdly isinstance(field.related_model, TimeSeries) doesn't work
                    time_series_fields.append(field.name)

        # create data frames with indices
        data = []
        for field in time_series_fields:
            data.append(getattr(self, field).to_dataframe())

        # concat dataframes of returned
        result = pd.concat(data, axis=1)
        return result


def unique_filename_user_directory(instance, filename):
    """
    Creates a unique filename using uuid and stores it into a user folder.
    File will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    :param instance:
    :param filename:
    :return:
    """

    # get file extension
    # todo: field validation must ensure that there is a .csv
    filename, file_ext = filename.rsplit('.', 1)

    # create new unique filename
    filename = 'user_{user_id}/{filename}_{uuid}.{ext}'.format(user_id=instance.user.id,
                                                               filename=filename,
                                                               uuid=uuid.uuid4(),
                                                               ext=file_ext)

    return filename


def csv_validator(file):
    """
    Checks if the uploaded file is a csv file and has a header (single row) using
    the Sniffer class from the Python csv module.
    :param file:
    :return:
    """

    csv_sniffer = csv.Sniffer()

    # read data and try to convert to string
    data = file.read(1024)

    try:
        data = data.decode(encoding='utf-8')
    except UnicodeDecodeError:
        raise ValidationError(_('File is either not a valid CSV or not encoded as UTF-8.'))

    try:
        dialect = csv_sniffer.sniff(data)
    except csv.Error:
        raise ValidationError(_('File is not a valid CSV file.'))

    has_header = csv_sniffer.has_header(data)
    if not has_header:
        raise ValidationError(_('CSV File has no header.'))

    # todo: check for actual column header names. write a class similar to https://stackoverflow.com/questions/20272579/django-validate-file-type-of-uploaded-file/27916582#27916582
    # reset read position of file
    file.seek(0)
    df = pd.read_csv(file, dialect=dialect, encoding='utf-8', header=[0], nrows=10)

    file.seek(0)
    # create a set of header columns and check if all necessary headers exist
    headers = set(df.columns)

    _specified_headers = ['index', 'wholesale_price', 'clean_fuel_price']

    for header in _specified_headers:
        if header not in headers:
            raise ValidationError(_('TimeSeries must contain the following columns: index, wholesale_price, clean_fuel_price'))


class CSVFileUpload(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    upload_date = models.DateTimeField(auto_created=True, auto_now_add=True)
    file = models.FileField(upload_to=unique_filename_user_directory,
                            validators=[csv_validator],
                            verbose_name='Time series CSV')
    # todo: create delimiter on save
    # delimiter = models.CharField(blank=False, max_length=2, default=',', verbose_name='Delimiter')

    def to_dataframe(self):
        # set pointer to beginning of file
        self.file.seek(0)

        # find csv dialect
        data = self.file.read(1024)

        data = data.decode(encoding='utf-8')

        csv_sniffer = csv.Sniffer()

        dialect = csv_sniffer.sniff(data)

        self.file.seek(0)

        return pd.read_csv(self.file, dialect=dialect)


class ThermalPlantOptimizationRun(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dispatch_model = models.ForeignKey(ThermalPlantDispatch, on_delete=models.CASCADE)
    started = models.DateTimeField(auto_now_add=True)
    simulation_time = models.IntegerField(null=True, verbose_name="Simulation time [s]")

    # configuration
    start = models.IntegerField(null=True, verbose_name="Offset for optimization run.")
    end = models.IntegerField(null=True, verbose_name="End of optimization run.")
    number_of_batches = models.IntegerField(null=True, verbose_name="Number of batches.")
    overlap = models.FloatField(null=True, verbose_name="Overlap between batches.")


class ThermalPlantOptimizationResult(models.Model):
    run = models.ForeignKey(ThermalPlantOptimizationRun, on_delete=models.CASCADE)

    # output fields
    production = models.FloatField(blank=False, verbose_name="Production [MWh]")
    consumption = models.FloatField(blank=False, verbose_name="Consumption [MWh]")

    ramping_BSE = models.FloatField(blank=False, verbose_name="Production during BSE ramping [MWh]")

    # input fields
    power_price = models.FloatField(blank=False, verbose_name="Wholesale power price [EUR/MWh]")
    fuel_price = models.FloatField(blank=False, verbose_name="Clean fuel price [EUR/MWh]")

    # todo: ask for definitions and expected values
    """
    ['production', 'consumption', 'powerProdBSE', 'powerProdRMP',
     'powerProdNRM', 'ONF', 'RMP', 'NRM', 'powerProdBSE_UP',
     'powerProdBSE_DW', 'powerProdRMP_UP', 'powerProdRMP_DW',
     'powerProdNRM_UP', 'powerProdNRM_DW', 'fuelCosts', 'rampingCosts',
     'depriciationCosts', 'Revenues', 'Costs', 'power_price', 'fuel_price']
    """