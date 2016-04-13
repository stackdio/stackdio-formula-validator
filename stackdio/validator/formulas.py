# -*- coding: utf-8 -*-

# Copyright 2016,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import copy
import os

import click
import yaml
from salt import config
from salt.grains import core
from salt.state import HighState


EXTRA_GRAINS = {
    'id': 'foo',
    'stack_id': 1,
    'roles': [],
    'domain': 'test.stackd.io',

    # Simulate centos 7
    'os_family': 'RedHat',
    'osmajorrelease': '7',
    'os': 'CentOS',
}

EXTRA_PILLAR = {
    '__stackdio__': {
        'users': [
            {
                'username': 'test.user',
                'ssh_key': 'ssh',
            }
        ]
    }
}


ACCEPTABLE_ERRORS = [
    'list object has no element 0',
]

WARNINGS = [
    'Detected conflicting IDs, SLS IDs need to be globally unique.',
    'in saltenv base is not available on the salt master or through a configured fileserver',
]


class CustomHighState(HighState):

    def merge_included_states(self, highstate, state, errors):
        # The extend members can not be treated as globally unique:
        if '__extend__' in state:
            highstate.setdefault('__extend__',
                                 []).extend(state.pop('__extend__'))
        if '__exclude__' in state:
            highstate.setdefault('__exclude__',
                                 []).extend(state.pop('__exclude__'))
        for id_ in state:
            if id_ in highstate:
                if highstate[id_] != state[id_]:
                    if highstate[id_]['__env__'] != state[id_]['__env__'] or \
                                    highstate[id_]['__sls__'] != state[id_]['__sls__']:
                        errors.append((
                            'Detected conflicting IDs, SLS'
                            ' IDs need to be globally unique.\n    The'
                            ' conflicting ID is {0!r} and is found in SLS'
                            ' \'{1}:{2}\' and SLS \'{3}:{4}\'').format(
                            id_,
                            highstate[id_]['__env__'],
                            highstate[id_]['__sls__'],
                            state[id_]['__env__'],
                            state[id_]['__sls__'])
                        )
        try:
            highstate.update(state)
        except ValueError:
            errors.append(
                'Error when rendering state with contents: {0}'.format(state)
            )


class FormulaValidator(object):

    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.default_pillar = {}
        self.highstate = None

        self.errors = []
        self.warnings = []

        if not os.path.isfile(os.path.join(root_dir, 'SPECFILE')):
            self.error('Formula does not contain a SPECFILE at it\'s root.')

    def error(self, msg):
        click.echo('ERROR: ' + msg)
        self.errors.append(msg)

    def warn(self, msg):
        click.echo('WARNING: ' + msg)
        self.warnings.append(msg)

    def validate(self):
        components = self.validate_specfile()

        # Grab minion opts
        opts = copy.deepcopy(config.DEFAULT_MINION_OPTS)

        # Put in our opts
        opts['cachedir'] = os.path.join(self.root_dir, '.cache', 'master')
        opts['file_client'] = 'local'
        opts['file_roots'] = {
            'base': [self.root_dir]
        }
        opts['renderer'] = config.DEFAULT_MASTER_OPTS['renderer']
        opts['state_top'] = config.DEFAULT_MASTER_OPTS['state_top']
        opts['id'] = 'test-master'

        core.__opts__ = opts

        grains = core.os_data()
        grains.update(EXTRA_GRAINS)

        opts['grains'] = grains

        self.highstate = CustomHighState(opts, self.default_pillar)

        for component in components:
            self.validate_component(component)

        return not self.errors

    def validate_specfile(self):
        with open(os.path.join(self.root_dir, 'SPECFILE')) as f:
            spec_yaml = yaml.safe_load(f)

        formula_title = spec_yaml.get('title')
        root_path = spec_yaml.get('root_path')
        components = spec_yaml.get('components')

        # Grab the default pillar
        self.default_pillar = spec_yaml.get('pillar_defaults', {})
        self.default_pillar.update(EXTRA_PILLAR)

        if formula_title is None:
            self.error('Formula must have a title in the SPECFILE.')

        if root_path is None:
            self.error('Formula must have a root_path in the SPECFILE.')

        if not os.path.isdir(os.path.join(self.root_dir, root_path)):
            self.error('Formula must have a directory named {} '
                       'at it\'s top level.'.format(root_path))

        if not isinstance(components, list) or len(components) == 0:
            self.error('components must be a non-empty list')

        return components

    def validate_component(self, component):
        if not isinstance(component, dict):
            self.error('Each entry in components must be a dict.')

        if 'title' not in component or 'sls_path' not in component:
            self.error('Each component must contain a title and an sls_path.')

        component_title = component['title']
        sls_path = component['sls_path'].replace('.', '/')
        init_file = os.path.join(sls_path, 'init.sls')
        sls_file = sls_path + '.sls'
        abs_init_file = os.path.join(self.root_dir, init_file)
        abs_sls_file = os.path.join(self.root_dir, sls_file)

        if not os.path.isfile(abs_init_file) and not os.path.isfile(abs_sls_file):
            self.error(
                'Could not locate an SLS file for component \'{0}\'. '
                'Expected to find either \'{1}\' or \'{2}\'.'.format(component_title,
                                                                     init_file,
                                                                     sls_file)
            )
            return

        # Make sure it renders
        self.highstate.push_active()
        try:
            high, errors = self.highstate.render_highstate({'base': [sls_path]})
        finally:
            self.highstate.pop_active()

        errors += self.highstate.state.verify_high(high)

        for error in errors:
            is_error = True
            for msg in ACCEPTABLE_ERRORS:
                if msg in error:
                    is_error = False
                    break

            is_warning = False
            for msg in WARNINGS:
                if msg in error:
                    is_warning = True
                    is_error = False
                    break

            if is_warning:
                self.warn(error)
                continue

            if is_error:
                self.error(error)
