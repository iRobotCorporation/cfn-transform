# cfn-transform

A class for creating transforms to CloudFormation templates.
A tranform is instantiated with a template, and when applied changes that template
in-place.
Subclasses generally implement transforms through two mechanisms.
A method named after a template section, that is, Metadata, Parameters, Mappings,
Conditions, Resources, or Outputs, can return a dict of entries to merge into that 
section. These methods are also a good place to modify those sections in arbitrary
ways.
If a method is defined named `process_resource`, it will be applied to the resources
in the template. A resource type spec (a string or regex object, or a list of those)
can be defined in the field `PROCESS_RESOURCE_TYPE_SPEC` to filter the resources processed.
If a more complex transform needs to be done that doesn't fit into those options, override the
`_apply` to replace the built-in transformation steps.

A transformer class is instantiated with a template as input. The `apply()` method should then
be called once (and only once; an exception will be raised if it is called again); this method
returns the template, but it is also accessible as the `template` property.

## Building executable transformers

There are two facilities for command line transforming of templates. Both require the
`file-transformer` library, available at https://github.com/benkehoe/file-transformer .

This library installs an executable, `cfn-transform`, that can load a 
`CloudFormationTemplateTransformer` subclass and apply it to a template from a file
or stdin. The script input can be used in the following ways:
```bash
cfn-transform SUBCLASS FILE_IN FILE_OUT
cfn-transform SUBCLASS FILE_IN [-o FILE_OUT]
cfn-transform SUBCLASS [-i FILE_IN] [-o FILE_OUT]
```
If FILE_IN or FILE_OUT are not provided, stdin or stdout will be used, respectively.

SUBCLASS must be specified as `PACKAGE_PATH[:CLASS_NAME]`. If the class is the
only subclass of `CloudFormationTemplateTransformer` in the package, it does
not need to be provided.

To create a custom script for a transformer subclass, use the `main()` class method.
This can be used directly with no arguments, for example in the `entry_points` section
of your `setup.py`, and this will use the basic `file-transformer` input/output arguments.

Any keyword arguments to the `main` method will get passed to the `file_transformer.main`
function. The primary use of this is to customize the input arguments. For this,
create an `argparse.ArgumentParser`, add the appropriate arguments, and then pass
it to the `main` method of the subclass as the `parser` keyword argument.
The parsed arguments will be available as a dict in the `options` field in the subclass. 

A subclass can override the `description` class method to provide the program description
when not providing your parser.