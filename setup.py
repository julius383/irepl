import setuptools

setuptools.setup(
    name="irepl",
    version="0.3.1",
    description="Wrapper to enhance any repl",
    author="Julius Kibunjia",
    author_email="kibunjiajulius@gmail.com",
    license="MIT",
    packages=setuptools.find_packages(),
    zip_safe=False,
    entry_points={"console_scripts": ["irepl = irepl:main", ]},
)
