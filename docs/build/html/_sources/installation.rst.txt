Installation
============

Once cloned NICE repository on your local host, just follows these steps in 
order to properly use the interface tools.

Prerequisites
-------------

NICE application is based on the Python3_ scripting language and Django3.0.5_
web framework. In order to correcly use its capabilities, make 
sure your Python version has been properly installed. Anyway you can find 
your prefered installation mode (e.g., the Python installation provided by 
your GNU/Linux distribution) and then check out your Python version through:

.. _Python3: https://www.python.org

.. _Django3.0.5: https://djangoproject.com

.. code-block:: bash

    $ python3 --version

Then verifies that it is major than Python 3.7!


Create and Set the Environment
------------------------------

Once gone on the path of your cloned NICE, let's move to the parent 
directory of the project. Now create the proper Python environment for the 
correct usage of the interface:

1. Create a Python3 environment called *venv-django-py3*, or whatever. 
   This should create a Python3 virtual environment with Pip installation functionalities:

.. code-block:: bash

    $ python3 -m venv venv-django-py3

2. Activate the environment:

.. code-block:: bash

    $ source venv-django-py3/bin/activate
    
3. Check check that *python* command returns the right version and that *pip* shows correctly the packages installed:

.. code-block:: bash

    $ python --version
    $ pip list

4. Install the requirements package from the *requirements.txt*:

.. code-block:: bash

    $ pip install -r <path-to-the-nice-package>/requirements.txt

5. Check that the previous steps have been completed succesfully. Entering the following command shouldn't return any error, warning etc:

.. code-block:: bash

    $ python -c "import numpy, django, pymysql, pandas, bokeh, gwdama"

If an encouraging message of success comes up, you can go the the next 
step.

Now you can setup the environment variables:

.. code-block:: bash

    $ source <path-to-the-nice-package>/setup_vmutils.sh
    
.. note::

   **This step must be done every time you refresh your terminal.** 

   Activate the environment:

      $ source <path-to-the-nice-parent-directory>/venv-django-py3/bin/activate
      
   Setup the environment variables:

      $ source  <path-to-the-nice-package>/setup_vmutils.sh

If everything has gone well, you should see something like this in your 
command line:

.. code-block:: bash

    (venv-django-py3) <user>@<host>:

The next step to do, in order to enjoy your glitch exploration, is the 
:doc:`glitch database configuration <configuration>`.
