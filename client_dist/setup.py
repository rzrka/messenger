from setuptools import setup, find_packages

setup(name='mess_client_rzrka',
      version='0.0.2',
      description='mess_client_rzrka',
      author='rzrka',
      author_email='rzrka@ya.ru',
      packages=find_packages(),
      install_requires=['PyQt5', 'sqlalchemy', 'pycryptodome', 'pycryptodomex']
      )