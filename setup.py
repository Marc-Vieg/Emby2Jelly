import os
import setuptools


# Declare your non-python data files:
# Files underneath shell/ will be copied into the build preserving the
# subdirectory structure if they exist.
data_files = []
#for root, dirs, files in os.walk('.'):
#    data_files.append((os.path.relpath(root, '.'),
#                       [os.path.join(root, f) for f in files]))

setuptools.setup(
    name='Emby2Jelly',
    version='0.0.1',
    author='Marc Vieg/Gunter Cobaye/Richard Schwab/Nothing4You/Nicola Canepa',
    author_email='canne74@gmail.com',
    description='Recreate users from emby to jellyfin and migrate their watched content for movies and TV shows',
    py_modules=["APImain"],
    # Enable these 2 lines (and disable the above) if package structure changes
    # packages=setuptools.find_packages('src', exclude=['.tox', 'test']),
    packages=[],
    # package_dir={"": "src"},
    data_files=data_files,
    install_requires=[
        'requests',
        'configobj',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    zip_safe=False,
    python_requires='>=3.6',
    entry_points={
        "console_scripts": [
            "emby2jelly = APImain:main",
        ],
    }
)


