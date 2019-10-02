
class MetaClass(type):
    def __new__(cls, clsname, superclasses, attributedict):
        print('clsname', clsname)
        print('superclasses', superclasses)
        print('attributedict', attributedict)
        return type.__new__(cls, clsname, superclasses, attributedict)


class TestClassBase:
    class Meta:
        django_object = None
        index = None
        fields = []


class TestClass2(TestClassBase, metaclass=MetaClass):
    pass


if __name__ == '__main__':
    t = TestClass2()