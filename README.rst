Pelican LESSCPY
===============

Plugin to generate minified CSS style sheets with integrity hashes for `Pelican
<https://blog.getpelican.com/>`_ using `LESSCPY
<https://pypi.org/project/lesscpy/>`_.

Options
-------

LESS_INTEGRITY
    List of hash algorithms to compute for the generated CSS Files

VERSIONED_CSS
    If true, then include a version query string in the final filename for each CSS file based on the sha256 hash of the generated file

LESS_CSS_FILES
    Dictionary with key value pairs of the form
    {name: (infilename, outfilename)}


Output
------

generator.context['compiled_css']
    Dictionary of the form {name: {'css_file': versioned_filename, 'integrity': integrity_string}}

    The final output is suitable for use in a Pelican template such as in the example below


.. code:: html
        {% for style, css_data in compiled_css.items() %}
         <link rel="stylesheet"
                      type="text/css"
                      integrity="{{ css_data.integrity }}"
                      href="{{ SITEURL }}/{{ css_data.css_file }}"/>
        {% endfor %}
