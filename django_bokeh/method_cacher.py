from functools import partial

class TestClass:
    def __init__(self):
        pass

    def filter(self, *args, **kwargs):
        args = ', '.join(args)

        print(kwargs)
        kwargs = ['{key}= {value}'.format(key=key, value=value) for key, value in kwargs.items()]

        print('filtering with ({args}) and ({kwargs})'.format(args=args, kwargs=kwargs))
        return None

    def get(self, *args, **kwargs):
        args = ', '.join(args)
        kwargs = ['{key}= {value}'.format(key=key, value=value) for key, value in kwargs.items()]

        print('getting with ({args}) and ({kwargs})'.format(args=args, kwargs=kwargs))
        return None


class DeferredMethodCall:
    def __init__(self, instance):
        self._instance = instance
        self._method_cache = []

    def __getattr__(self, item):
        """
        Check if the object instance has the attribute and if it is callable.
        If the attribute is a method then cache it.
        :param item:
        :return:
        """
        if hasattr(self._instance, item):
            _attr = getattr(self._instance, item)
            if callable(_attr):
                # if it is a method then cache it (return function to call)
                return partial(self.cache_method_call, item)

            else:
                # if it is an attribute
                return _attr

        else:
            raise AttributeError('Instance does not have method {method}'.format(method=item))

    def cache_method_call(self, method_name, *args, **kwargs):
        """
        Cache method call and return self (for chaining).
        :param method_name:
        :param args:
        :param kwargs:
        :return:
        """
        self._method_cache.append((method_name, args, kwargs))
        return self

    def eval(self):
        """
        Evaluate the cached methods on the instance.
        :return:
        """

        for cached_method in self._method_cache:
            method_name = cached_method[0]
            args = cached_method[1]
            kwargs = cached_method[2]

            # get method from instance
            method = getattr(self._instance, method_name)

            # call method with cached args, kwargs
            method(*args, **kwargs)


if __name__ == '__main__':
    t = TestClass()

    dm = DeferredMethodCall(t)

    dm.filter('arg1', arg2='testen').filter('arg3', arg4='testen')

    print(dm._method_cache)

    dm.eval()