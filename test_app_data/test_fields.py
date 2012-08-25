from django.test import TestCase
from django.conf import settings

from nose import tools

from app_data.registry import NamespaceConflict, NamespaceMissing, app_registry

from .models import Article, Publishable, Category

class AppDataContainer(dict):
    pass


class DummyAppDataContainer(AppDataContainer):
    pass


class DummyAppDataContainer2(AppDataContainer):
    pass


class TestAppData(TestCase):
    def tearDown(self):
        super(TestAppData, self).tearDown()
        if hasattr(settings, 'APP_DATA_CLASSES'):
            del settings.APP_DATA_CLASSES
        app_registry._reset()
        app_registry.default_class = None

    def test_classes_can_be_overriden_from_settings(self):
        settings.APP_DATA_CLASSES = {
                'global': {'testing': 'test_app_data.test_fields.DummyAppDataContainer'},
                'test_app_data.publishable': {'testing': 'test_app_data.test_fields.DummyAppDataContainer2'}
            }
        # re-initialize app_registry
        app_registry._reset()

        art = Article()
        inst = Category()
        art.app_data = {'testing': {'answer': 42}}
        inst.app_data = {'testing': {'answer': 42}}

        tools.assert_true(isinstance(art.app_data['testing'], DummyAppDataContainer2))
        tools.assert_true(isinstance(inst.app_data['testing'], DummyAppDataContainer))

    def test_registered_classes_can_behave_as_attrs(self):
        app_registry.register('dummy', DummyAppDataContainer)
        art = Article()
        tools.assert_true(isinstance(art.app_data.dummy, DummyAppDataContainer))

    def test_registered_classes_can_be_set_as_attrs(self):
        app_registry.register('dummy', DummyAppDataContainer)
        art = Article()
        art.app_data.dummy = {'answer': 42}
        tools.assert_true(isinstance(art.app_data.dummy, DummyAppDataContainer))
        tools.assert_equals(DummyAppDataContainer({'answer': 42}), art.app_data.dummy)
        tools.assert_equals({'dummy': {'answer': 42}}, art.app_data)

    def test_registered_classes_get_stored_on_access(self):
        app_registry.register('dummy', DummyAppDataContainer)
        art = Article()
        art.app_data['dummy']
        tools.assert_equals({'dummy': {}}, art.app_data)

    @tools.raises(NamespaceConflict)
    def test_namespace_can_only_be_registered_once(self):
        app_registry.register('dummy', DummyAppDataContainer)
        app_registry.register('dummy', DummyAppDataContainer2)

    @tools.raises(NamespaceMissing)
    def test_unregistered_namespace_cannot_be_unregistered(self):
        app_registry.register('dummy', DummyAppDataContainer)
        app_registry.unregister('dummy')
        app_registry.unregister('dummy')

    def test_override_class_for_model_only(self):
        app_registry.register('dummy', DummyAppDataContainer)
        app_registry.register('dummy', DummyAppDataContainer2, model=Publishable)
        inst = Publishable()
        tools.assert_true(isinstance(inst.app_data.get('dummy', {}), DummyAppDataContainer2))

    def test_get_app_data_returns_registered_class_instance(self):
        app_registry.register('dummy', DummyAppDataContainer)
        inst = Publishable()
        tools.assert_true(isinstance(inst.app_data.get('dummy', {}), DummyAppDataContainer))

    def test_existing_values_get_wrapped_in_proper_class(self):
        app_registry.register('dummy', DummyAppDataContainer)
        inst = Publishable()
        inst.app_data = {'dummy': {'hullo': 'there'}}
        tools.assert_true(isinstance(inst.app_data['dummy'], DummyAppDataContainer))

    def test_get_app_data_returns_default_class_if_not_registered(self):
        app_registry.default_class = AppDataContainer
        inst = Publishable()
        tools.assert_true(isinstance(inst.app_data.get('dummy', {}), AppDataContainer))

    def test_app_data_container_behaves_like_dict(self):
        inst = Publishable()
        data = inst.app_data.get('dummy', {})
        data['foo'] = 'bar'
        tools.assert_equals(data['foo'], 'bar')
        tools.assert_equals(data.keys(), ['foo'])
        tools.assert_equals(data.values(), ['bar'])