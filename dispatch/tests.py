import datetime
import numpy as np

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User

from .models import TimeSeries, TimeSeriesIndex, ThermalPlant, CompressedJSONModel, ThermalPlantDispatch, create_thermal_plant_dispatch_model
from .utils import to_dict


def create_dummy_time_series_data(length):
    index = [item for item in range(length)]
    price = list(15+7*np.random.rand(length))
    clear_fuel_price = list(30+7*np.random.rand(length))

    return index, price, clear_fuel_price


class ThermalPlantDispatchTests(TestCase):
    def test_create_thermal_plant_dispatch_instance(self):
        # create dummy user
        user = create_dummy_user()

        # create time series data
        index, wholesale_price, clean_fuel_price = create_dummy_time_series_data(10)

        print(index, wholesale_price, clean_fuel_price)

        # create dummy plant
        plant = create_thermal_plant(user)
        plant_definition = plant.to_dict()

        # create
        thermal_plant_dispatch_setup = create_thermal_plant_dispatch_model(user,
                                                                           0,
                                                                           plant_definition,
                                                                           index,
                                                                           wholesale_price,
                                                                           clean_fuel_price,
                                                                           pk=None)

        print(to_dict(thermal_plant_dispatch_setup))

        print(thermal_plant_dispatch_setup.time_series())

        print(thermal_plant_dispatch_setup.__data_fields__)

        print(type(thermal_plant_dispatch_setup.clean_fuel_price))


class CompressedJSONModelTests(TestCase):
    def test_create_field(self):
        # create list of values to store
        value = [item for item in range(10)]

        # create and save
        instance = CompressedJSONModel.objects.create(value=value)

        # retrieve from db
        retrieved_instance = CompressedJSONModel.objects.get()

        self.assertEqual(value, retrieved_instance.value)


# ThermalPlantTests
def create_thermal_plant(user):
    d = {'user': user,
         'capacity': 100,
         'efficiency': 0.5,
         'MIN_prod_fraction': 0.2,
         'SEL_prod_fraction': 0.8,
         'MEL_prod_fraction': 1.0,
         'ramping_rate_BSE': 0,
         'ramping_rate_RMP': 0.025,
         'ramping_rate_NRM': 0.1,
         'ramping_costs_BSE': 30,
         'ramping_costs_RMP': 25,
         'ramping_costs_NRM': 20,
         'depreciation': 2,
         'shutdown_costs': 0,
         'hot_start_costs': 20,
         'warm_start_costs': 21,
         'cold_start_costs': 22,
         'hot_start_within_timedelta': 3,
         'warm_start_within_timedelta': 12}

    thermal_plant = ThermalPlant.objects.create(**d)

    return thermal_plant


class ThermalPlantTests(TestCase):
    def test_creation(self):
        user = create_dummy_user()

        plant = create_thermal_plant(user)

        self.assertIs(plant.MIN == plant.capacity * plant.MIN_prod_fraction, True)

    def test_conversion_to_dictionary(self):
        user = create_dummy_user()

        plant = create_thermal_plant(user)

        plant_dict = plant.to_dict()

        print(plant_dict)

        # todo: what to test here? that all fields are there? that they have certain values?


# Create your tests here.
def create_dummy_user():
    user = User.objects.create_user(username='Dummy', password='123456')
    return user


def create_time_series_index(start, interval):
    return TimeSeriesIndex.objects.create(index_type=2, datetime_start=start, datetime_interval=interval)


def create_integer_time_series_index(offset):
    return TimeSeriesIndex.objects.create(index_type=1, integer_offset=offset)

def create_datetime_index(length):
    start = datetime.datetime(1990, 1, 1, 0, tzinfo=datetime.timezone.utc)
    interval = datetime.timedelta(hours=1)
    length = 10
    expected_result = start + interval * np.arange(length)
    return expected_result

def create_time_series(name, length, user, time_series_index, data=b''):
    obj = TimeSeries.objects.create(
        user=user,
        name=name,
        index=time_series_index,
        length=length,
        data=data,
    )

    return obj


class TimeSeriesIndexTests(TestCase):
    def test_create_time_series_index_from_integer_index(self):
        length = 10
        index, price, fuel_price = create_dummy_time_series_data(length)

        time_series_index = TimeSeriesIndex()

        time_series_index.create_from_data(index)

        time_series_index.save()

        retrieved_time_series = TimeSeriesIndex.objects.get(pk=1)

        created_index = retrieved_time_series.create_index(length)

        self.assertIs(all(index == created_index), True)

    def test_create_time_series_index_from_datetime_index(self):
        length = 10
        index = create_datetime_index(length)

        time_series_index = TimeSeriesIndex()

        time_series_index.create_from_data(index)

        time_series_index.save()

        retrieved_time_series = TimeSeriesIndex.objects.get(pk=1)

        created_index = retrieved_time_series.create_index(length)

        self.assertIs(all(index == created_index), True)

    def test_time_series_index_does_exist(self):
        length = 10
        index = create_datetime_index(length)

        time_series_index = TimeSeriesIndex()

        time_series_index.create_from_data(index)

        time_series_index.save()

        # new instance
        time_series_index = TimeSeriesIndex()

        time_series_index = time_series_index.does_exist(index)

        created_index = time_series_index.create_index(length)

        self.assertIs(all(index == created_index), True)


class TimeSeriesTests(TestCase):
    def test_create_time_series_index(self):
        """
        Tests the creation of a time series index.
        :return:
        """
        user = User.objects.create_user(username='Dummy', password='123456')

        print(type(user), user)

        start = datetime.datetime(1990, 1, 1, 0, tzinfo=datetime.timezone.utc)
        interval = datetime.timedelta(hours=1)
        length = 10
        expected_result = start + interval * np.arange(length)

        time_series_index = create_time_series_index(start,
                                                     interval)

        time_series = create_time_series('test', length, user, time_series_index)

        print(time_series.create_index())
        print(expected_result)
        print(np.array_equal(time_series.create_index(), expected_result))
        self.assertIs(np.array_equal(time_series.create_index(), expected_result), True)

    def test_create_integer_index(self):
        user = User.objects.create_user(username='Dummy', password='123456')

        print(type(user), user)

        offset = 10
        length = 10
        expected_result = offset + np.arange(length)

        integer_index = create_integer_time_series_index(offset)

        time_series = create_time_series('test', length, user, integer_index)

        print(time_series.create_index())
        print(expected_result)
        self.assertIs(np.array_equal(time_series.create_index(), expected_result), True)
