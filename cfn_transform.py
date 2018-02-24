"""Library for creating transforms to CloudFormation templates.

Copyright 2018 iRobot Corporation

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

__version__ = '0.9.0'

import collections
import argparse
import sys
import importlib
import inspect
import six

import yaml

class CloudFormationTemplateTransform(object):
    """A class for creating transforms to CloudFormation templates.
    A tranform is instantiated with a template, and when applied changes that template
    in-place.
    Subclasses generally implement transforms through two mechanisms.
    A method named after a template section, that is, Metadata, Parameters, Mappings,
    Conditions, Resources, or Outputs, can return a dict of entries to merge into that 
    section. These methods are also a good place to modify those sections in arbitrary
    ways.
    If a method is defined named process_resource, it will be applied to the resources
    in the template. A resource type spec (a string or regex object, or a list of those)
    can be defined in the field PROCESS_RESOURCE_TYPE_SPEC to filter the resources processed.
    If a more complex transform needs to be done that doesn't fit into those options, an
    _apply method can be defined that will replace the built-in transformation steps.
    """
    
    @classmethod
    def resource_type_matches(cls, resource_type, resource_type_spec):
        """Check a resource type matches the type spec. The type spec can be:
        - a string
        - a regex (uses search, not match)
        - a callable returning a bool
        - an iterable of type specs
        """
        if resource_type_spec is None:
            return True
        if isinstance(resource_type_spec, six.string_types):
            return resource_type == resource_type_spec
        elif hasattr(resource_type_spec, 'search'):
            return resource_type_spec.search(resource_type)
        elif callable(resource_type_spec):
            return resource_type_spec(resource_type)
        elif isinstance(resource_type_spec, collections.Iterable):
            return any(cls.resource_type_matches(resource_type, spec) for spec in resource_type_spec)
        else:
            raise TypeError("Unknown resource_type_spec {}".format(resource_type_spec))
    
    @classmethod
    def map(cls, resources, func, resource_type_spec):
        remove = []
        add = {}
        for logical_id, resource in six.iteritems(resources):
            if cls.resource_type_matches(resource['Type'], resource_type_spec):
                new_resources = func(logical_id, resource)
                add.update(new_resources or {})
                if not resource:
                    remove.append(logical_id)
        for logical_id in remove:
            del resources[logical_id]
        _merge_dicts(resources, add)
        return resources
        
    
    def __init__(self, template, options={}):
        self.template = template
        self.options = options
        self._remaining_args = options.get('remaining_args', [])
        self.applied = False
    
    def subtransformers(self):
        return []
    
    def Description(self):
        return None
    
    def Metadata(self):
        return {}
    
    def Parameters(self):
        return {}
    
    def Mappings(self):
        return {}
    
    def Conditions(self):
        return {}
    
    def Transform(self):
        return None
    
    def Resources(self):
        return {}
    
    def Outputs(self):
        return {}
    
    def apply(self):
        """Apply the transform to the template. In general, should only be called once.
        The transform is applied as follows:
        - subtransformers
        - sections: All section methods (Resources, etc.) are called and their outputs
            are merged into the template
        - process_resource: If the class has a process_resource method, it is applied
            to each resource in the template.
          - If a field PROCESS_RESOURCE_TYPE_SPEC is defined, it is used to filter the
            resources.
          - The process_resource method receives the resource logical id and the resource
            definition. It can return a dict of new resources to add. Emptying the
            contents of the input resource will cause it to be removed.
        Hooks can be provided for the above steps by defining methods named update_before_X
        or update_after_X, and additionally update_at_start and update_at_end. These
        are called with no arguments.
        
        Instead of overriding this method to perform more complex transforms, override the
        _apply method, which will preserve the housekeeping that this class performs.
        """
        if self.applied:
            raise RuntimeError("Transform applied more than once")
        
        self._apply()
        
        self.applied = True
        
        return self.template
    
    def _run_hook(self, *args):
        for name in args:
            method_name = 'update_{}'.format(name)
            if hasattr(self, method_name):
                getattr(self, method_name)()
    
    def _apply(self):
        
        
        self._run_hook('at_start', 'before_subtransformers')
        
        for subtransformer in self.subtransformers():
            if inspect.isclass(subtransformer):
                subtransformer = subtransformer(self.template)
            self.template = subtransformer.apply()
        
        self._run_hook('after_subtransformers', 'before_sections')
        
        desc = self.Description()
        if desc is not None:
            self.template['Description'] = desc
        
        transforms = self.Transform()
        if transforms:
            if 'Transform' not in self.template:
                self.template['Transform'] = []
            if isinstance(transforms, six.string_types):
                self.template['Transform'].append(transforms)
            else:
                self.template['Transform'].extend(transforms)
        
        dict_fields = ['Metadata', 'Parameters', 'Mappings', 'Conditions', 'Resources', 'Outputs']
        
        for field in dict_fields:
            if field not in self.template:
                self.template[field] = {}
            value = getattr(self, field)()
            _merge_dicts(self.template[field], value)
        
        for field in dict_fields + ['Description', 'Transform']:
            if field in self.template and not self.template[field]:
                del self.template[field]
        
        self._run_hook('after_sections', 'before_process_resource')
        
        if hasattr(self, 'process_resource'):
            self.map(self.template['Resources'], self.process_resource, resource_type_spec=getattr(self, 'PROCESS_RESOURCE_TYPE_SPEC', None))
        
        self._run_hook('after_process_resource')
        
        self._run_hook('at_end')
    
    @classmethod
    def main(cls, **kwargs):
        """Run the given CloudFormationTemplateTransform class
        against commandline inputs, supporting both files and stdin/out.
        Keyword args are passed to file_transformer.main()
        """
        try:
            import file_transformer
        except Exception as e:
            sys.exit("{}\nSee https://github.com/benkehoe/file-transformer".format(e))
        
        def loader(input_stream, args):
            return yaml.load(input_stream)
        
        def processor(input, args):
            transform = cls(input, vars(args))
            transform.apply()
            return transform.template
        
        def dumper(output, output_stream, args):
            yaml.dump(output, output_stream)
        
        return file_transformer.main(processor, loader, dumper, **kwargs)
    
    @classmethod
    def _subclass_main(cls, args=None):
        parser = argparse.ArgumentParser()
    
        parser.add_argument('transform_class')
        
        args, remaining_args = parser.parse_known_args(args=args)
        
        xform = args.transform_class.split(':')

        try:
            if len(xform) == 2:
                pkg_name, cls_name = xform
                module = importlib.import_module(pkg_name)
                subcls = getattr(module, cls_name)
            elif len(xform) == 1:
                pkg_name = xform[0]
                module = importlib.import_module(pkg_name)
                subcls = inspect.getmembers(module, lambda o: (
                    inspect.isclass(o) 
                    and issubclass(o, cls)
                    and o is not cls))
                if len(subcls) == 0:
                    parser.exit("No {} subclass found in {}".format(cls.__name__, pkg_name))
                elif len(subcls) > 1:
                    names = [name for name, _ in subcls]
                    parser.exit("Multiple transforms found in {}, please choose from: {}".format(pkg_name, ' '.join(names)))
                else:
                    subcls = subcls[0][1]
            else:
                parser.exit("Improperly formatted transform specifier")
        except Exception as e:
#             import traceback
#             traceback.print_exception(*sys.exc_info())
            parser.exit("Exception importing transform class: {}".format(e))
        
        return subcls.main(args=remaining_args)
    
    @classmethod
    def get_lambda_handler(cls):
        def handler(event, context):
            import boto3
            
            def resolve_location(location):
                if isinstance(location, dict):
                    bucket = location['Bucket']
                    key = location['Key']
                else:
                    raise ValueError("Unknown location {}".format(location))
                return bucket, key
            
            if 'TemplateBody' in event:
                template_body = event['TemplateBody']
                if isinstance(template_body, six.string_types):
                    template = template_body
                else:
                    template = yaml.safe_load(template_body)
            elif 'TemplateURL' in event:
                template_url = event['TemplateURL']
                raise NotImplementedError
            elif 'TemplateLocation' in event:
                bucket, key = resolve_location(event['TemplateLocation'])
                client = boto3.client('s3')
                response = client.get_object(Bucket=bucket, Key=key)
                template = yaml.load(response['Body'])
                template = yaml.safe_load(template_body)
            
            transform = cls(template, options={'Context': context})
            
            transformed = transform.apply()
            
            if 'OutputLocation' not in event:
                return transformed
            
            transformed_str = yaml.dump(transformed)
            bucket, key = resolve_location(event['OutputLocation'])
            client = boto3.client('s3')
            response = client.put_object(Bucket=bucket, Key=key, Body=transformed_str)
        return handler
        

def module_main():
    return CloudFormationTemplateTransform._subclass_main()
        
def _merge_dicts(dict1, dict2, path=None):
    """Recursively merge dict2 into dict1 (in place)"""
    if path is None:
        path = []
    for key, value2 in six.iteritems(dict2):
        if key not in dict1:
            dict1[key] = value2
            continue
        value1 = dict1[key]
        if value1 == value2:
            continue
        elif isinstance(value1, dict) and isinstance(value2, dict):
            _merge_dicts(dict1[key], dict2[key], path=path+[key])
        elif isinstance(value1, (set, frozenset)) and isinstance(value2, (set, frozenset, list)):
            dict1[key] = value1 | frozenset(value2)
        else:
            raise TypeError("Cannot merge {} with {} at {}".format(type(value1), type(value2), '/'.join(path)))
    return dict1