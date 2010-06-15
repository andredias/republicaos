try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='republicaos',
    version='0.1',
    description='',
    author='André Felipe Dias',
    author_email='andref.dias@pronus.eng.br',
    url='http://www.republicaos.com.br',
    install_requires=[
        "Pylons>=1.0",
        "Elixir>=0.7", 
        "SQLAlchemy>=0.6",
        "Genshi>=0.4",
        "Elixir>=0.6.1",
        "DateUtilsl>=0.4",
        "pytz", 
        "Babel",
        "http://geopy.googlecode.com/svn/trunk/",
    ],
    setup_requires=["PasteScript>=1.6.3"],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    package_data={'republicaos': ['i18n/*/LC_MESSAGES/*.mo']},
    #message_extractors={'republicaos': [
    #        ('**.py', 'python', None),
    #        ('public/**', 'ignore', None)]},
    zip_safe=False,
    paster_plugins=['Elixir', 'PasteScript', 'Pylons', 'Shabti'],
    entry_points="""
    [paste.app_factory]
    main = republicaos.config.middleware:make_app

    [paste.app_install]
    main = pylons.util:PylonsInstaller
    """,
)
