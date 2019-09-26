from pyomo.environ import Var, Param
import pandas as pd

import os
from pyutilib.services import register_executable


def register_cbc_executable(path=r'C:\Users\Benjamin\PycharmProjects\DispatchModels\dispatch\solver'):
    """

    :param path:
    :return:
    """
    # todo: add cbc executable path to Django settings
    path_cbc = path
    os.environ['PATH'] += os.pathsep + path_cbc
    register_executable(name='cbc')
    return None


def convert_model_result_to_dataframe(model):
    result = []

    # add results of variables, parameters to data frame
    for component_type in [Var, Param]:
        for component in model.component_objects(component_type, active=True):
            try:
                # use a dict to create a series from (index, value) pairs returned by var
                s = pd.Series({key: value.value for key, value in component.items()}, name=component.name)
                result.append(s)
            except:
                # Params are directly values
                # use a dict to create a series from (index, value) pairs returned by var
                s = pd.Series({key: value for key, value in component.items()}, name=component.name)
                result.append(s)

    result = pd.concat(result, axis=1)

    return result


def append_result_to_df(df, new_results):
    return pd.concat([df, new_results], axis=0)

