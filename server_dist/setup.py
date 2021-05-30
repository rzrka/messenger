from setuptools import setup, find_packages

setup(name='mess_server_rzrka',
      version='0.0.2',
      description='mess_server_rzrka',
      author='rzrka',
      author_email='rzrka@ya.ru',
      packages=find_packages(),
      install_requires=['PyQt5', 'sqlalchemy', 'pycryptodome', 'pycryptodomex']
      )