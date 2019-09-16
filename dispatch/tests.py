import datetime
import numpy as np

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User

from .models import TimeSeries, TimeSeriesIndex


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
