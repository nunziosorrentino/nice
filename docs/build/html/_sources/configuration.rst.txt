Configuration
=============

Once installed the NICE application on your host, it is time for the local 
database. NICE provides some simulated glitches metadata, which represent
a starting point for showing its functionalities. Let's see how to
fill a local database.

MySQL Database Service
----------------------

MySQL_ is used for the NICE Databases management and is supported by 
both Django_ and Pymysql_ libraries.

.. _MySQL: https://www.mysql.com/

.. _Django: https://www.djangoproject.com/

.. _Pymysql: https://pymysql.readthedocs.io/en/latest/

Ensure you have it installed:

.. code-block:: bash
   
   $ sudo apt-get update
   $ sudo apt-get upgrade
   $ sudo apt-get install mysql-server
   
Adjust mysql security installation with the following command:

.. code-block:: bash
   
   $ sudo mysql_secure_installation
   
Here press *y* to the provided questions, set the password security to *0* level (if asked), and 
create your mysql *root* password. 

**Remember your mysql root password**, it is fundamental for the next steps. 

Make sure you can access to the MySQL shell as a root:

.. code-block:: bash
   
   $ sudo mysql -u root -p
   
Enter root password and check you are in *mysql>* shell.

Now let's create the required MySQL user and associate it to
the needed privileges. Consider *vm_admin* as user name.  
This will be used for the database connection from the *localhost*.
Let's call:

{PASSWORD}: the password associated to the *vm_admin*; 
(*WARNING*: this is different from the root password you created before);

Once you choose the user password, create an empty database named *glitches_db* as root user:

.. code-block:: bash

   $ sudo mysql -u root -e "CREATE USER 'vm_admin'@'localhost' IDENTIFIED BY '{PASSWORD}';"
   $ sudo mysql -u root -e "CREATE DATABASE glitches_db;"
   $ sudo mysql -u root -e "GRANT SELECT, INSERT, ALTER, CREATE, REFERENCES, INDEX, UPDATE ON glitches_db.* TO 'vm_admin'@'localhost';"
   
Check that user has been correctly created with:

.. code-block:: bash

   $ sudo mysql -u vm_admin -p 
   
Enter {PASSWORD} and if you are in *mysql>* shell check if *glitches_db* is accessible with:

 .. code-block:: bash

   mysql> show databases; 
   
**This database will be filled with the simulated glitches metadata.**

The database connection to the NICE interface is made using the Django
framework. Go to settings directory:

.. code-block:: bash

   $ cd <path-to-nice-project>/virgo_glitches/settings/
   
and create a *.env* file. Here set the environment variable *PASSWORD*
equal to one you chose for the *vm_admin* user:

PASSWORD={PASSWORD}

Database Creation and Connection
--------------------------------

Go to the NICE project directory!

The NICE database structure is set using the Django migrations
modules. The models of such structure are located in the *monitor/models.py*
script and can be created and migrated to *glitches_db*  with the 
following commands:

.. code-block:: bash

   $ python manage.py makemigrations monitor --settings=virgo_glitches.settings.local
   
this should create models related to glitches, classes, channels, detector
and pipelines with which the catalogue is interfaced.

Now migrate this structure to the NICE database with:

.. code-block:: bash

   $ python manage.py migrate --settings=virgo_glitches.settings.local  

If no errors rise up, the structure of database is done, but it is still empty!

Let's see how too fill it with simulated glitches metadata.

Insert Glitches
---------------

There are 2000 of simulated glitches in *<path-to-nice-project>/data/ListGlitchMetadata*
directory and are stored in:

1. **singauss.hdf5**: glitches modelled with a sin-gaussian time function;
2. **scattered_light.hdf5**: arches glitches due to the laser scattered light in the interferometers;

Use *load_glitches.py* executable in order to fill the database with the
corresponding metadata;

.. code-block:: bash

   $ load_glitches.py <path/to/glitch/parameters/file.hdf5> --gclass {GWCLASS} --pipeline GWSkySim
   
where '{GWCLASS}' is *GWScattLight* or *GWSinGauss*, depending on the *hdf5* file you are loading.
It will create tables elements  compatible with the catalogue models provided by Django.

Ensure you can connect to the database by running NICE on Django server:

.. code-block:: bash

   $ python manage.py runserver --settings=virgo_glitches.settings.local
   
If it returns a link to the NICE webpage at port 8000, the database is 
correctly connected to the application.

Go to the link page and 
:doc:`explore the NICE application tools <investigationflow>` interacting with
the glitch metadata presented in the database.  


