Template-y
===========

Template-Y is as the name suggests a template for how to build your own bot, based on one of the core bots provided
in Program-Y. The reason for this template and structure is to allow you to create your own aiml, set, map and rdf files
and keep them in a folder schema that maps back to Program-Y but allows Program-Y repo to be updates and pulled from
GitHub without it conflicting with your own Bot development.

Each folder in this template contains a README.txt explaining the reason for the folder, the contents it should
contain and how to specifiy the correct config options to keep the 2 folders seperate.


Naming Your Project
--------------------
Obviously no one wants to create bot/project named templatey. So you need to some manual tweaking of folders and config
files as follows. Assumption here is that the top level folder is the name of your project

    1) Rename template-y to NAMEOFPROJECT, the name of the bot/project you want to call it

    2) Rename src/templatey to /src/NAMEOFPROJECT

    3) Rename test/templatey to /test/NAMEOFPROJECT

    4) Replace any reference to templatey in config.yaml with NAMEOFPROJECT

    5) Replace any reference to templatey in logging.yaml with NAMEOFPROJECT

    6) Replace any reference to templatey in console.sh with NAMEOFPROJECT

In addition there are some config options you can decide on in config.yaml

    1) Decide which overrides you want by switching the following config items
         overrides:
           allow_system_aiml: false
           allow_learn_aiml: false
           allow_learnf_aiml: false

    2) Specify the location of the learnf file if you set allow_learnf_aiml to true in overrides

         defaults:
          learn-filename: ./aiml/learnf.aiml

    3) Decide if you want to generate a braintree. xml file by uncommenting the following lines
        #braintree:
        #  file: ./braintree.xml
        #  content: xml
       See the Program-Y for more details about what the braintree can be used for

    4) Check you .sh or .cmd file t ensure that paths are correct
        Template-y installs at the same level as program-y
        Therefore the python paths and relative paths in config assume
        that program-y is reached via the relative path ../program-y
        If you install program-y and/or template in different paths to these
        then you will need to adjust
