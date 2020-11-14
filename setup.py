import setuptools

setuptools.setup(
    name="ihf",
    version="0.1.5",
    description="ihf",
    long_description="I Hate Front and API. IHF is a library for create quickly and easily real-time secure webapp",
    url="https://github.com/Hantlowt/ihf",
    packages=setuptools.find_packages(),
    py_modules=['ihf'],
    install_requires=['websockets', 'bs4', 'singleton-decorator'],
    include_package_data=True
)
