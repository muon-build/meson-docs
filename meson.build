project('meson-docs')

python = import('python').find_installation('python3', modules: ['yaml'])

genrefman = [python, meson.project_source_root() / 'docs/genrefman.py']

meson_docs_h = custom_target(
    output: 'meson_docs.h',
    command: [
        genrefman,
        '-q',
        '-l', 'fastyaml',
        '-g', 'c',
        '-o', '@OUTPUT@',
        '--no-modules',
    ],
)
