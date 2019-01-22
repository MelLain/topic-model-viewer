# Topic Model Processor (2019)

from __future__ import print_function

import sys
import os.path
import tempfile
import shutil
import subprocess
import argparse

from setuptools import setup, find_packages
from distutils.spawn import find_executable
from distutils.command.build import build as _build

def find_protoc_exec():
    # extract path to protobuf executable from command-line arguments
    argument_prefix = "protoc_executable"

    parser = argparse.ArgumentParser(description="", add_help=False)
    parser.add_argument("--{}".format(argument_prefix), action="store")
    found_args, rest_args = parser.parse_known_args(sys.argv)
    sys.argv = rest_args

    result = vars(found_args).get(argument_prefix, None)
    if result is not None and os.path.exists(result):
        return result

    # try to guess from environment variables
    if 'PROTOC' in os.environ and os.path.exists(os.environ['PROTOC']):
        return os.environ['PROTOC']

    # try to find using distutils helper function
    return find_executable("protoc")

protoc_exec = find_protoc_exec()

def generate_proto_files(
        src_folder,
        src_proto_file,
        dst_py_file):
    """
    Generates pb2.py files from corresponding .proto files
    """

    source_file = os.path.join(src_folder, src_proto_file)
    output_file = dst_py_file

    if (not os.path.exists(output_file) or
            os.path.exists(output_file) and
            os.path.getmtime(source_file) > os.path.getmtime(output_file)):
        print("Generating {}...".format(dst_py_file))

        if not os.path.exists(source_file):
            sys.stderr.write("Can't find required file: {}\n".format(
                source_file))
            sys.exit(-1)

        if not protoc_exec:
            raise ValueError("No protobuf compiler executable was found!")

        try:
            tmp_dir = tempfile.mkdtemp(dir="./")
            protoc_command = [
                protoc_exec,
                "-I" + src_folder,
                "--python_out=" + tmp_dir,
                source_file]
            print("Executing {}...".format(protoc_command))
            if subprocess.call(protoc_command):
                raise
            src_py_file = src_proto_file.replace(".proto", "_pb2.py")
            if os.path.exists(dst_py_file):
                os.remove(dst_py_file)
            os.rename(os.path.join(tmp_dir, src_py_file), dst_py_file)
        finally:
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir)

class build(_build):
    def run(self):
        generate_proto_files(
            '.',
            "./messages.proto",
            "./topic_model_processor/messages_pb2.py")

        _build.run(self)

setup_kwargs = dict(
    name='topic_model_processor',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[
        'pandas',
        'numpy'
    ],
    setup_requires=[
        'numpy'
    ],
    cmdclass={'build': build},
)

setup(**setup_kwargs)

