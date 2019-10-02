"""
Task: Easy creation of plots from django models.

Subtasks:
1. Create a base class for creation of bokeh plots which abstracts the creation process and defines hooks for
performing individual steps. Note: define most common workflow for simple plots. think about how is it extendable.
2. Create a concrete line function plotting class based on the abstract base class.
3. Create a Meta class which allows to bind a django model and certain parameters to the bokeh plotting class.

Note:
    - Question: How shall the filtering of the underlying django class be managed. Restriction of only showing user specific
    values. Maybe using a .queryset method which contains a class that can be interfaced like Cls.objects but just records all
    filters and such and then later (lazely) processes them when the data is needed. It's like bounding the underlying
    django model. 



"""