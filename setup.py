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
        'Beaker==1.5.3',
        'DateUtils==0.5.1',
        'decorator==3.2.0',
        'Elixir==0.7.1',
        'FormEncode==1.2.2',
        'Genshi==0.6',
        'MiniMock==1.2.5',
        'PasteDeploy==1.3.3',
        'PasteScript==1.7.3',
        'Pylons==1.0',
        'python_dateutil==1.5',
        'pytz',
        'Routes==1.12.3',
        'SQLAlchemy==0.6.1',
        'Tempita==0.4',
        'WebError==0.10.2',
        'WebHelpers==1.0',
        'WebOb==0.9.8',
        'WebTest==1.2.1',
        "Babel==0.9.5",
        "http://geopy.googlecode.com/svn/trunk/",
        ],
    setup_requires=["PasteScript>=1.7.3"],
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
