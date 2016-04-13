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

import click

from .formulas import FormulaValidator


@click.command()
@click.argument('root_path',
                type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True))
def main(root_path):
    validator = FormulaValidator(root_path)

    if not validator.validate():
        raise click.Abort('Errors found in formula.')


if __name__ == '__main__':
    main()
