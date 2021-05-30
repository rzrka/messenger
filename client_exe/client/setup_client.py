import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    'packages': ['mainapp', 'log', 'client', 'unit_test'],
}
setup(
    name='mess_client',
    version='0.8.8',
    description='mess_client',
    options={
        'build_exe': build_exe_options
    },
    executables=[Executable('client.py',
                            base='Win32GUI',
                            target_name='client.exe',
                            )]
)