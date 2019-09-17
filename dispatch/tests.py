import datetime
import numpy as np

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User

from .models import TimeSeries, TimeSeriesIndex, ThermalPlant
from .utils import to_dict

# ThermalPlantTests
def create_thermal_plant(user):
    d = {}

    d['user'] = user
    d['capacity'] = 100
    d['efficiency'] = 0.5
    d['MIN_prod_fraction'] = 0.2
    d['SEL_prod_fraction'] = 0.8
    d['MEL_prod_fraction'] = 1.0
    d['ramping_rate_BSE'] = 0
    d['ramping_rate_RMP'] = 0.025
    d['ramping_rate_NRM'] = 0.1
    d['ramping_costs_BSE'] = 30
    d['ramping_costs_RMP'] = 25
    d['ramping_costs_NRM'] = 20
    d['depreciation'] = 2
    d['shutdown_costs'] = 0
    d['hot_start_costs'] = 20
    d['warm_start_costs'] = 21
    d['cold_start_costs'] = 22
    d['hot_start_within_timedelta'] = 3
    d['warm_start_within_timedelta'] = 12

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

        plant_dict = to_dict(plant)

        print(plant_dict)

        # todo: what to test here? that all fields are there? that they have certain values?


# Create your tests here.
def create_dummy_user():
    user = User.objects.create_user(username='Dummy', password='123456')
    return user


def create_time_series_index(start, interval):
    return TimeSeriesIndex.objects.create(index_type=2, datetime_start=start, datetime_interval=interval)


def create_integer_index(offset):
    return TimeSeriesIndex.objects.create(index_type=1, integer_offset=offset)


def create_time_series(name, length, user, time_series_index, data=b''):
    obj = TimeSeries.objects.create(
        user=user,
        name=name,
        index=time_series_index,
        length=length,
        data=data,
    )

    return obj


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

        integer_index = create_integer_index(offset)

        time_series = create_time_series('test', length, user, integer_index)

        print(time_series.create_index())
        print(expected_result)
        self.assertIs(np.array_equal(time_series.create_index(), expected_result), True)
