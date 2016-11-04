# ChaoticaTools
Tools I use to edit or manipulate Chaotica's XML files.


# GradientInject

The program will recursively travel through a root directory and attempt to find a filename that you pass in on the command line.

It expects that you have an Apophysis flame (with the desired gradient) in your clipboard, and will inject it into the Chaotica file.  A new file called `<chaotica_file_name>_gradiated.chaos` will be created, and will overwrite any exisiting files with the same name.

# XaosInject

This will update xaos loops between transforms in a Chaotica file in two passes;

* The first pass normalizes the transform names for sanity in parsing.
* The second pass actually updates the xaos information of the flame.

The program will recursively travel through a root directory and attempt to find a filename that you pass in on the command line.
After the first pass, it will ask for you to load the file to verify what the iterator numbers are so you link the correct iterators.

Make sure you pass in the original file name - not the name of the "_rewritten" file - when you're on the second pass!

When you run the program again, you'll then be prompted to enter a mode;

* `copy=<from_what>,<to what>`; so copying the settings of the first transform to the second would be `copy=1,2`
* `using=a,b,c`;  so copying the xaos loops between transforms 1, 2, and 3 would be done by `using=1,2,3`

The final file that is generated is `<input_file_name>_xaosed.chaos`


# reverseEngineerGrad

This expects you to copy the XML from Chaotica into your clipboard via `Edit->Copy XML to Clipboard`.
It will then parse through the file you have, attempt to approximate the pallete entries into HSV nodes, and insert the gradient into your clipboard.  This gradient is possible to open and edit in Ultrafractal.

At the moment, this does is not compatible with Chaotica's palettes, and thus requires the parameters to include a gradient.

# varsearch

This will recursively traverse through the root directory of the file and locate all chaotica files containing the variation you specify on the command line.
