# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 The Meson development team
from __future__ import annotations

from pathlib import Path
from .generatorbase import GeneratorBase
from .model import (
	ReferenceManual,
	Function,
)

OBJ_MAP = {
	'build_machine': 'machine',
	'build_tgt': 'build_target',
	'cfg_data': 'configuration_data',
	'cmake': None,
	'cmake_options': None,
	'custom_idx': None,
	'custom_tgt': 'custom_target',
	'dep': 'dependency',
	'env': 'environment',
	'feature': 'feature_opt',
	'int': 'number',
	'list': 'array',
	'runresult': 'run_result',
	'str': 'string',
	'program': 'external_program',
}

class GeneratorC(GeneratorBase):
	def __init__(self, manual: ReferenceManual, out: Path, enable_modules: bool) -> None:
		super().__init__(manual)
		self.out = out
		self.enable_modules = enable_modules

	def _cstr(self, s: str) -> str:
		s = s.replace('\\', '\\\\')
		s = s.replace('\n', '\\n')
		s = s.replace('"', '\\"')
		return f'"{s}"'

	def _wrap(self, s):
		return f"{{ {s} }}"

	def _cstr_struct(self, d):
		elems = []
		for k, v in d.items():
			if v is True:
				s = "true"
			elif v is False:
				s = "false"
			elif type(v) is int:
				s = str(v)
			else:
				s = self._cstr(v)

			elems.append(f".{k} = {s}")

		return self._wrap(', '.join(elems))

	def _generate_function(self, func: Function) -> tuple[dict, list, list]:
		posargs = []
		kwargs = []

		for arg in func.posargs:
			posargs.append({
				'common.name': arg.name,
				'common.description': arg.description,
			})

		for arg in func.optargs:
			posargs.append({
				'common.name': arg.name,
				'common.description': arg.description,
			})

		if func.varargs:
			posargs.append({
				'common.name': func.varargs.name,
				'common.description': func.varargs.description,
			})

		for arg in self.sorted_and_filtered(list(func.kwargs.values())):
			kwargs.append({
				'common.name': arg.name,
				'common.description': arg.description,
			})

		return {
			'common.name': func.name,
			'common.description': func.description,
			'posargs_len': len(posargs),
			'kwargs_len': len(kwargs),
		}, posargs, kwargs

	def generate(self) -> None:
		prefix = 'meson_doc_'
		text = ''

		posargs = []
		kwargs = []
		funcs = { '0': [] }

		def add_function(group_name, func):
			f, p, k = self._generate_function(func)
			f['posargs_start'] = len(posargs)
			f['kwargs_start'] = len(kwargs)
			funcs[group_name].append(self._cstr_struct(f))
			posargs.extend([self._cstr_struct(x) for x in p])
			kwargs.extend([self._cstr_struct(x) for x in k])

		for x in self.sorted_and_filtered(self.functions):
			add_function('0', x)

		for x in self.sorted_and_filtered(self.objects):
			if x.name in OBJ_MAP:
				o = OBJ_MAP[x.name]
			else:
				o = x.name

			if o is None:
				continue

			o = f'obj_{o}'

			for y in self.sorted_and_filtered(x.methods):
				if o not in funcs:
					funcs[o] = []
				add_function(o, y)

		text += f'struct {prefix}entry_arg {prefix}posargs[] = {{\n'
		for o in posargs:
			text += f'\t{o},\n'

		text += '};\n'

		text += f'struct {prefix}entry_arg {prefix}kwargs[] = {{\n'
		for o in kwargs:
			text += f'\t{o},\n'

		text += '};\n'

		for o in funcs:
			text += f'struct {prefix}entry_func {prefix}object_{o}[] = {{\n'

			for f in funcs[o]:
				text += '\t' + f + ',\n'

			text += '\t{ 0 },\n'

			text += '};\n\n'

		text += f'struct {prefix}entry_func *{prefix}root[obj_type_count] = {{\n'

		for o in funcs:
			text += f'\t[{o}] = {prefix}object_{o},\n'

		text += '};\n'

		self.out.write_text(
			text.lstrip(),
			encoding='utf-8',
		)
